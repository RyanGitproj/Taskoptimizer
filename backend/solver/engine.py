"""
Module solver.engine
--------------------
Moteur d'optimisation basé sur Google OR-Tools (CP-SAT).
Responsabilité unique : transformer des activités en un planning optimisé
sans aucun couplage avec la couche API ou service.
"""

from dataclasses import dataclass
from typing import List, Tuple
from ortools.sat.python import cp_model


# ---------------------------------------------------------------------------
# Structures de données internes au solveur
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TacheEntree:
    id: int
    nom: str
    duree: int          # en minutes
    priorite: int       # 1–5
    est_flexible: bool
    debut_souhaite: int | None  # en minutes depuis minuit, None si flexible


@dataclass(frozen=True)
class PlageResolue:
    id: int
    nom: str
    debut: int   # en minutes depuis minuit
    fin: int     # en minutes depuis minuit
    priorite: int
    est_flexible: bool
    est_pause: bool = False


@dataclass(frozen=True)
class ResultatSolveur:
    planifiees: List[PlageResolue]
    non_planifiees: List[str]
    score: float


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PRIORITE_PAUSE = 0
NOM_PAUSE = "Pause"

# Coefficient de pondération pour les priorités dans la fonction objectif
POIDS_PRIORITE = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}


# ---------------------------------------------------------------------------
# Moteur CP-SAT
# ---------------------------------------------------------------------------

class MoteurOptimisation:
    """
    Encapsule toute la logique OR-Tools.
    Utilise le solveur CP-SAT pour planifier les tâches sans chevauchement,
    dans une fenêtre horaire définie, en maximisant la satisfaction des priorités.
    """

    def __init__(
        self,
        debut_journee: int,
        fin_journee: int,
        duree_pause: int,
        seuil_pause: int = 120,
    ):
        self.debut_journee = debut_journee
        self.fin_journee = fin_journee
        self.duree_pause = duree_pause
        self.seuil_pause = seuil_pause  # durée de travail continu avant pause forcée

    # ------------------------------------------------------------------
    # Point d'entrée public
    # ------------------------------------------------------------------

    def resoudre(self, taches: List[TacheEntree]) -> ResultatSolveur:
        modele = cp_model.CpModel()
        horizon = self.fin_journee  # borne supérieure absolue en minutes

        # Étape 1: Découper les tâches longues (>90 min)
        taches_decoupees = self._decouper_taches_longues(taches)

        # Variables de décision : intervalle [début, fin] et booléen "planifiée"
        vars_taches = self._creer_variables(modele, taches_decoupees, horizon)

        # Contrainte 1 : pas de chevauchement
        self._contrainte_pas_chevauchement(modele, vars_taches)

        # Contrainte 2 : respect de la fenêtre de travail
        self._contrainte_fenetre_travail(modele, vars_taches)

        # Contrainte 3 : ancrage des tâches fixes
        self._contrainte_ancrage_fixe(modele, taches_decoupees, vars_taches)

        # Fonction objectif : maximiser la somme pondérée des tâches planifiées
        self._definir_objectif(modele, taches_decoupees, vars_taches)

        # Résolution
        solveur = cp_model.CpSolver()
        solveur.parameters.max_time_in_seconds = 25.0
        # Configuration déterministe pour reproducibilité
        solveur.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
        solveur.parameters.cp_model_presolve = True
        solveur.parameters.linearization_level = 0
        solveur.parameters.num_search_workers = 1  # Un seul worker pour déterminisme
        statut = solveur.Solve(modele)

        return self._extraire_resultat(solveur, statut, taches_decoupees, vars_taches)

    # ------------------------------------------------------------------
    # Construction du modèle
    # ------------------------------------------------------------------

    def _decouper_taches_longues(self, taches: List[TacheEntree]) -> List[TacheEntree]:
        """Découpe les tâches >90 min en exactement 2 segments entiers."""
        taches_decoupees = []
        max_id = max([t.id for t in taches]) if taches else 0
        next_id = max_id + 1

        for t in taches:
            if t.duree > 90:
                # Découpage en 2 segments entiers
                segment1_duree = t.duree // 2
                segment2_duree = t.duree - segment1_duree

                # Premier segment
                segment1 = TacheEntree(
                    id=next_id,
                    nom=f"{t.nom} (partie 1)",
                    duree=segment1_duree,
                    priorite=t.priorite,
                    est_flexible=t.est_flexible,
                    debut_souhaite=t.debut_souhaite,
                )
                taches_decoupees.append(segment1)
                next_id += 1

                # Deuxième segment
                segment2 = TacheEntree(
                    id=next_id,
                    nom=f"{t.nom} (partie 2)",
                    duree=segment2_duree,
                    priorite=t.priorite,
                    est_flexible=t.est_flexible,
                    debut_souhaite=t.debut_souhaite,
                )
                taches_decoupees.append(segment2)
                next_id += 1
            else:
                taches_decoupees.append(t)

        return taches_decoupees

    def _creer_variables(
        self, modele: cp_model.CpModel, taches: List[TacheEntree], horizon: int
    ) -> List[dict]:
        vars_liste = []
        for t in taches:
            debut = modele.NewIntVar(self.debut_journee, horizon, f"debut_{t.id}")
            fin = modele.NewIntVar(self.debut_journee, horizon, f"fin_{t.id}")
            planifiee = modele.NewBoolVar(f"planifiee_{t.id}")

            # Intervalle optionnel : la tâche peut être exclue si planifiee=0
            intervalle = modele.NewOptionalIntervalVar(
                debut, t.duree, fin, planifiee, f"intervalle_{t.id}"
            )

            vars_liste.append({
                "debut": debut,
                "fin": fin,
                "planifiee": planifiee,
                "intervalle": intervalle,
            })
        return vars_liste

    def _contrainte_pas_chevauchement(
        self, modele: cp_model.CpModel, vars_taches: List[dict]
    ):
        intervalles = [v["intervalle"] for v in vars_taches]
        modele.AddNoOverlap(intervalles)

    def _contrainte_fenetre_travail(
        self, modele: cp_model.CpModel, vars_taches: List[dict]
    ):
        for v in vars_taches:
            # début >= début journée si planifiée
            modele.Add(v["debut"] >= self.debut_journee).OnlyEnforceIf(v["planifiee"])
            # fin <= fin journée si planifiée
            modele.Add(v["fin"] <= self.fin_journee).OnlyEnforceIf(v["planifiee"])

    def _contrainte_ancrage_fixe(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ):
        for i, t in enumerate(taches):
            if not t.est_flexible and t.debut_souhaite is not None:
                # Si la tâche est planifiée, elle DOIT commencer à l'heure souhaitée
                modele.Add(vars_taches[i]["debut"] == t.debut_souhaite).OnlyEnforceIf(
                    vars_taches[i]["planifiee"]
                )

    def _definir_objectif(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ):
        termes = []
        for i, t in enumerate(taches):
            poids = POIDS_PRIORITE.get(t.priorite, t.priorite)
            termes.append(poids * vars_taches[i]["planifiee"])
        modele.Maximize(sum(termes))

    # ------------------------------------------------------------------
    # Extraction des résultats
    # ------------------------------------------------------------------

    def _extraire_resultat(
        self,
        solveur: cp_model.CpSolver,
        statut: int,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ) -> ResultatSolveur:
        statuts_valides = (cp_model.OPTIMAL, cp_model.FEASIBLE)
        if statut not in statuts_valides:
            return ResultatSolveur(planifiees=[], non_planifiees=[t.nom for t in taches], score=0.0)

        planifiees: List[PlageResolue] = []
        non_planifiees: List[str] = []
        score_total = 0.0
        score_max = sum(POIDS_PRIORITE.get(t.priorite, t.priorite) for t in taches)

        for i, t in enumerate(taches):
            if solveur.Value(vars_taches[i]["planifiee"]):
                debut = int(solveur.Value(vars_taches[i]["debut"]))
                fin = int(solveur.Value(vars_taches[i]["fin"]))
                planifiees.append(PlageResolue(
                    id=t.id,
                    nom=t.nom,
                    debut=debut,
                    fin=fin,
                    priorite=t.priorite,
                    est_flexible=t.est_flexible,
                    est_pause=(t.nom == NOM_PAUSE),
                ))
                score_total += POIDS_PRIORITE.get(t.priorite, t.priorite)
            else:
                # La pause ne doit jamais être non planifiée
                if t.nom != NOM_PAUSE:
                    non_planifiees.append(t.nom)

        # Tri chronologique
        planifiees.sort(key=lambda p: p.debut)

        # Normalisation : garantir un ordre canonique unique
        planifiees = self._normaliser_planning(planifiees)

        # Insérer les pauses basées sur l'ordre chronologique réel
        planifiees_avec_pauses = self._inserer_pauses_post_resolution(planifiees)

        # Validation finale : détecter et corriger les chevauchements
        planifiees_avec_pauses = self._valider_et_corriger_chevauchements(planifiees_avec_pauses)

        score_pct = round((score_total / score_max) * 100, 1) if score_max > 0 else 0.0

        return ResultatSolveur(
            planifiees=planifiees_avec_pauses,
            non_planifiees=non_planifiees,
            score=score_pct,
        )

    def _normaliser_planning(self, planifiees: List[PlageResolue]) -> List[PlageResolue]:
        """
        Normalise le planning pour garantir un ordre canonique unique.
        Trie par debut, puis par fin (jamais par ID).
        """
        # Tri strictement temporel : debut, puis fin
        planifiees.sort(key=lambda p: (p.debut, p.fin))
        return planifiees

    def _inserer_pauses_post_resolution(self, planifiees: List[PlageResolue]) -> List[PlageResolue]:
        """
        Insère les pauses après résolution basées sur l'ordre chronologique réel.
        Applique les règles de productivité sur l'ordre final déterminé par le solveur.
        Recalcul linéaire du planning après insertion des pauses.
        """
        if self.duree_pause <= 0 or not planifiees:
            return planifiees

        # Étape 1: Identifier où insérer les pauses basées sur les règles
        indices_pauses = []
        consecutive_sans_pause = 0
        derniere_tache_origine = None

        for i, plage in enumerate(planifiees):
            # Extraire le nom de la tâche originale (sans "(partie X)")
            nom_origine = plage.nom.split(" (partie")[0] if " (partie" in plage.nom else plage.nom
            
            # Si c'est une nouvelle tâche originale (pas un segment de la précédente)
            if nom_origine != derniere_tache_origine:
                consecutive_sans_pause += 1
                derniere_tache_origine = nom_origine
            
            # Règle 1: Pause après tâche longue (≥60 min)
            if plage.fin - plage.debut >= 60:
                indices_pauses.append(i + 1)
                consecutive_sans_pause = 0
                continue

            # Règle 2: Max 2 tâches consécutives sans pause
            if consecutive_sans_pause >= 2:
                indices_pauses.append(i + 1)
                consecutive_sans_pause = 0

        # Étape 2: Insérer les pauses aux positions identifiées
        pauses_a_inserer = []
        next_id = 10000
        for idx in indices_pauses:
            pauses_a_inserer.append((idx, next_id))
            next_id += 1

        # Étape 3: Recalcul linéaire du planning avec pauses insérées
        return self._recalculer_avec_pauses(planifiees, pauses_a_inserer)

    def _recalculer_avec_pauses(self, planifiees: List[PlageResolue], pauses_a_inserer: List[Tuple[int, int]]) -> List[PlageResolue]:
        """
        Recalcule linéairement le planning en insérant les pauses aux positions spécifiées.
        Garantit un ordre chronologique strict et aucun chevauchement.
        """
        resultat = []
        decalage_total = 0
        pause_idx = 0
        
        for i, plage in enumerate(planifiees):
            # Insérer les pauses qui doivent venir avant cette tâche
            while pause_idx < len(pauses_a_inserer) and pauses_a_inserer[pause_idx][0] == i:
                _, pause_id = pauses_a_inserer[pause_idx]
                # La pause commence à la fin de la tâche précédente (ou au début de la journée)
                debut_pause = resultat[-1].fin if resultat else self.debut_journee
                pause = PlageResolue(
                    id=pause_id,
                    nom=NOM_PAUSE,
                    debut=debut_pause,
                    fin=debut_pause + self.duree_pause,
                    priorite=PRIORITE_PAUSE,
                    est_flexible=True,
                    est_pause=True,
                )
                resultat.append(pause)
                decalage_total += self.duree_pause
                pause_idx += 1
            
            # Ajouter la tâche avec décalage
            plage_decalee = PlageResolue(
                id=plage.id,
                nom=plage.nom,
                debut=plage.debut + decalage_total,
                fin=plage.fin + decalage_total,
                priorite=plage.priorite,
                est_flexible=plage.est_flexible,
                est_pause=plage.est_pause,
            )
            resultat.append(plage_decalee)
        
        # Insérer les pauses restantes à la fin
        while pause_idx < len(pauses_a_inserer):
            _, pause_id = pauses_a_inserer[pause_idx]
            debut_pause = resultat[-1].fin
            pause = PlageResolue(
                id=pause_id,
                nom=NOM_PAUSE,
                debut=debut_pause,
                fin=debut_pause + self.duree_pause,
                priorite=PRIORITE_PAUSE,
                est_flexible=True,
                est_pause=True,
            )
            resultat.append(pause)
            pause_idx += 1
        
        return resultat

    def _valider_et_corriger_chevauchements(self, planifiees: List[PlageResolue]) -> List[PlageResolue]:
        """
        Valide qu'il n'y a pas de chevauchements et corrige si nécessaire.
        Recalcul linéaire fallback safe.
        """
        if not planifiees:
            return planifiees

        # Vérifier les chevauchements
        for i in range(len(planifiees) - 1):
            actuel = planifiees[i]
            suivant = planifiees[i + 1]
            
            # Si chevauchement détecté (fin actuel > debut suivant)
            if actuel.fin > suivant.debut:
                # Recalcul linéaire pour corriger
                return self._recalcul_lineaire_safe(planifiees)
        
        return planifiees

    def _recalcul_lineaire_safe(self, planifiees: List[PlageResolue]) -> List[PlageResolue]:
        """
        Recalcul linéaire safe : garantit aucun chevauchement.
        Préserve les pauses comme entités distinctes et immuables.
        """
        if not planifiees:
            return planifiees

        resultat = []
        temps_courant = planifiees[0].debut

        for plage in planifiees:
            duree = plage.fin - plage.debut
            
            # Les pauses sont immuables : on ne modifie jamais leur durée
            if plage.est_pause:
                plage_corrige = PlageResolue(
                    id=plage.id,
                    nom=plage.nom,
                    debut=temps_courant,
                    fin=temps_courant + self.duree_pause,  # Toujours duree_pause standard
                    priorite=plage.priorite,
                    est_flexible=plage.est_flexible,
                    est_pause=True,
                )
            else:
                # Tâches : on préserve leur durée originale
                plage_corrige = PlageResolue(
                    id=plage.id,
                    nom=plage.nom,
                    debut=temps_courant,
                    fin=temps_courant + duree,
                    priorite=plage.priorite,
                    est_flexible=plage.est_flexible,
                    est_pause=False,
                )
            
            resultat.append(plage_corrige)
            temps_courant = plage_corrige.fin

        return resultat

    def _creer_variables(
        self, modele: cp_model.CpModel, taches: List[TacheEntree], horizon: int
    ) -> List[dict]:
        vars_liste = []
        for t in taches:
            debut = modele.NewIntVar(self.debut_journee, horizon, f"debut_{t.id}")
            fin = modele.NewIntVar(self.debut_journee, horizon, f"fin_{t.id}")
            planifiee = modele.NewBoolVar(f"planifiee_{t.id}")

            # Intervalle optionnel : la tâche peut être exclue si planifiee=0
            intervalle = modele.NewOptionalIntervalVar(
                debut, t.duree, fin, planifiee, f"intervalle_{t.id}"
            )

            vars_liste.append({
                "debut": debut,
                "fin": fin,
                "planifiee": planifiee,
                "intervalle": intervalle,
            })
        return vars_liste
