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
    overflow: bool = False
    overflow_reason: str = ""


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

        # Contrainte 2.5 : minimiser le temps de fin max des tâches flexibles
        self._contrainte_minimiser_fin_flexible(modele, taches_decoupees, vars_taches)

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

    def _contrainte_minimiser_fin_flexible(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ):
        """Minimize the maximum end time of flexible tasks to encourage even distribution."""
        flexible_fins = []
        for i, t in enumerate(taches):
            if t.est_flexible:
                # Add end time to list if task is planned
                flexible_fins.append(vars_taches[i]["fin"])
        
        if flexible_fins:
            # Create a variable for the maximum end time
            max_fin_flexible = modele.NewIntVar(self.debut_journee, self.fin_journee, "max_fin_flexible")
            
            # Constraint: max_fin_flexible >= each flexible task's end time
            for fin in flexible_fins:
                modele.Add(max_fin_flexible >= fin)
            
            # Store this variable to use in the objective
            self.max_fin_flexible = max_fin_flexible

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
        
        # Add objective to minimize maximum end time of flexible tasks
        # This encourages flexible tasks to be distributed evenly across the day
        if hasattr(self, 'max_fin_flexible'):
            # Very small weight to avoid skipping tasks
            termes.append(-self.max_fin_flexible * 0.01)
        
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
                
                # Check for overflow and mark instead of rejecting
                overflow = False
                overflow_reason = ""
                if fin > self.fin_journee:
                    overflow = True
                    if t.est_flexible:
                        overflow_reason = "flexible_fit_last_slot"
                        print(f"[WARNING] Flexible task '{t.nom}' exceeds fin_journee ({self.fin_journee}), marked as overflow")
                    else:
                        overflow_reason = "fixed_task_exceeds_window"
                        print(f"[WARNING] Fixed task '{t.nom}' exceeds fin_journee ({self.fin_journee}), marked as overflow")
                
                planifiees.append(PlageResolue(
                    id=t.id,
                    nom=t.nom,
                    debut=debut,
                    fin=fin,
                    priorite=t.priorite,
                    est_flexible=t.est_flexible,
                    est_pause=(t.nom == NOM_PAUSE),
                    overflow=overflow,
                    overflow_reason=overflow_reason,
                ))
                score_total += POIDS_PRIORITE.get(t.priorite, t.priorite)
            else:
                # La pause ne doit jamais être non planifiée
                if t.nom != NOM_PAUSE:
                    non_planifiees.append(t.nom)

        # Tri chronologique
        planifiees.sort(key=lambda p: p.debut)

        # Debug: log task order after normalization (BEFORE pauses)
        print("[DEBUG] Task order after normalization (BEFORE pauses):")
        for p in planifiees:
            print(f"  {p.nom}: debut={p.debut}, fin={p.fin}, duree={p.fin - p.debut}, flexible={p.est_flexible}")

        # Normalisation : garantir un ordre canonique unique
        planifiees = self._normaliser_planning(planifiees)

        # Insérer les pauses basées sur l'ordre chronologique réel
        planifiees_avec_pauses = self._inserer_pauses_post_resolution(planifiees)

        # Debug: log task order after pauses
        print("[DEBUG] Task order after pauses:")
        for p in planifiees_avec_pauses:
            print(f"  {p.nom}: debut={p.debut}, fin={p.fin}, duree={p.fin - p.debut}, est_pause={p.est_pause}")

        # Validation: detect unjustified gaps
        for i in range(len(planifiees_avec_pauses) - 1):
            actuel = planifiees_avec_pauses[i]
            suivant = planifiees_avec_pauses[i + 1]
            gap = suivant.debut - actuel.fin
            if gap > 30 and not actuel.est_pause and not suivant.est_pause:
                print(f"[WARNING] Unjustified gap detected: {gap} min between '{actuel.nom}' ({actuel.fin}) and '{suivant.nom}' ({suivant.debut})")

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
        Renomme les parties de tâches selon l'ordre chronologique.
        """
        # Tri strictement temporel : debut, puis fin
        planifiees.sort(key=lambda p: (p.debut, p.fin))
        
        # Renommer les parties de tâches selon l'ordre chronologique
        # pour éviter "partie 2" avant "partie 1"
        task_parts = {}
        for p in planifiees:
            if " (partie" in p.nom:
                base_name = p.nom.split(" (partie")[0]
                if base_name not in task_parts:
                    task_parts[base_name] = []
                task_parts[base_name].append(p)
        
        # Create new instances with renamed parts
        result = []
        for p in planifiees:
            new_p = p
            # Check if this task is part of a split task
            for base_name, parts in task_parts.items():
                if p in parts and len(parts) > 1:
                    # Find the position of this part in chronological order
                    sorted_parts = sorted(parts, key=lambda x: x.debut)
                    position = sorted_parts.index(p)
                    new_p = PlageResolue(
                        id=p.id,
                        nom=f"{base_name} (partie {position + 1})",
                        debut=p.debut,
                        fin=p.fin,
                        priorite=p.priorite,
                        est_flexible=p.est_flexible,
                        est_pause=p.est_pause,
                        overflow=p.overflow,
                        overflow_reason=p.overflow_reason,
                    )
                    break
            result.append(new_p)
        
        return result

    def _inserer_pauses_post_resolution(self, planifiees: List[PlageResolue]) -> List[PlageResolue]:
        """
        Insère les pauses après résolution basées sur l'ordre chronologique réel.
        Applique les règles de productivité sur l'ordre final déterminé par le solveur.
        Recalcul linéaire du planning après insertion des pauses.
        Les pauses sont optionnelles et ne sont insérées que si le temps disponible le permet.
        
        NOUVELLE LOGIQUE:
        - OR-Tools gère UNIQUEMENT les tâches
        - Les pauses sont en post-processing avec contraintes intelligentes
        - Pauses ajoutées SEULEMENT SI:
          * au moins 2 blocs de travail consécutifs existent
          * OU durée cumulée de travail > seuil (90 min)
        - Jamais de pause si planning trop fragmenté
        - Jamais de pause si cela force un overflow
        - Jamais de pause si temps restant insuffisant
        """
        if self.duree_pause <= 0 or not planifiees:
            return planifiees

        # Calculate task fill rate
        temps_total_taches = sum(p.fin - p.debut for p in planifiees if not p.est_pause)
        duree_journee = self.fin_journee - self.debut_journee
        fill_rate = temps_total_taches / duree_journee
        
        print(f"[DEBUG] Task fill rate: {fill_rate:.2%} ({temps_total_taches}/{duree_journee} min)")
        print(f"[DEBUG] Non-pause tasks: {[(p.nom, p.fin-p.debut) for p in planifiees if not p.est_pause]}")
        
        # Only insert pauses if fill rate is below 70% (i.e., there's significant slack time)
        if fill_rate >= 0.7:
            print(f"[DEBUG] Skipping all pauses (fill rate {fill_rate:.2%} >= 70%)")
            return planifiees

        # Check for fragmentation: if too many small tasks, skip pauses
        nombre_taches = len([p for p in planifiees if not p.est_pause])
        if nombre_taches > 6:
            print(f"[DEBUG] Skipping pauses (too many tasks: {nombre_taches} > 6)")
            return planifiees

        # Étape 1: Identifier où insérer les pauses basées sur les nouvelles règles
        indices_pauses = []
        consecutive_sans_pause = 0
        derniere_tache_origine = None
        duree_cumulee = 0
        blocs_consecutifs = 0

        for i, plage in enumerate(planifiees):
            # Extraire le nom de la tâche originale (sans "(partie X)")
            nom_origine = plage.nom.split(" (partie")[0] if " (partie" in plage.nom else plage.nom
            duree_tache = plage.fin - plage.debut
            
            # Si c'est une nouvelle tâche originale (pas un segment de la précédente)
            if nom_origine != derniere_tache_origine:
                consecutive_sans_pause += 1
                derniere_tache_origine = nom_origine
                blocs_consecutifs += 1
                duree_cumulee += duree_tache
            
            # NOUVELLE RÈGLE 1: Pause si au moins 2 blocs de travail consécutifs
            if blocs_consecutifs >= 2:
                indices_pauses.append(i + 1)
                consecutive_sans_pause = 0
                blocs_consecutifs = 0
                duree_cumulee = 0
                print(f"[DEBUG] Pause candidate at position {i+1} (2 consecutive blocks)")
                continue
            
            # NOUVELLE RÈGLE 2: Pause si durée cumulée de travail > 90 min
            if duree_cumulee >= 90:
                indices_pauses.append(i + 1)
                consecutive_sans_pause = 0
                blocs_consecutifs = 0
                duree_cumulee = 0
                print(f"[DEBUG] Pause candidate at position {i+1} (cumulative work: {duree_cumulee} min)")
                continue
            
            # Règle de secours: Pause après tâche longue (≥90 min)
            if duree_tache >= 90:
                indices_pauses.append(i + 1)
                consecutive_sans_pause = 0
                blocs_consecutifs = 0
                duree_cumulee = 0
                print(f"[DEBUG] Pause candidate at position {i+1} (long task: {duree_tache} min)")

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
        Les pauses sont optionnelles et ne sont insérées que si le temps disponible le permet.
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
                fin_pause = debut_pause + self.duree_pause
                
                # Check if adding this pause would cause overflow for ANY remaining task
                # Calculate the total time needed for all remaining tasks including this pause
                temps_restant_total = sum(p.fin - p.debut for p in planifiees[i:])
                temps_disponible = self.fin_journee - debut_pause
                slack_time = temps_disponible - temps_restant_total - self.duree_pause
                
                # Only insert pause if there's significant slack time (at least 30 minutes)
                # This ensures pauses are only added when there's genuinely extra time available
                if slack_time >= 30:
                    pause = PlageResolue(
                        id=pause_id,
                        nom=NOM_PAUSE,
                        debut=debut_pause,
                        fin=fin_pause,
                        priorite=PRIORITE_PAUSE,
                        est_flexible=True,
                        est_pause=True,
                        overflow=False,
                        overflow_reason="",
                    )
                    resultat.append(pause)
                    decalage_total += self.duree_pause
                    print(f"[DEBUG] Pause inserted at {debut_pause}-{fin_pause} (time available: {temps_disponible} min, needed: {temps_restant_total + self.duree_pause} min)")
                else:
                    print(f"[DEBUG] Pause skipped at {debut_pause} (not enough time: {temps_disponible} min available, {temps_restant_total + self.duree_pause} min needed)")
                
                pause_idx += 1
            
            # Ajouter la tâche avec décalage
            nouvelle_fin = plage.fin + decalage_total
            # Safety check: mark tasks that exceed fin_journee as overflow instead of skipping
            overflow = plage.overflow or (nouvelle_fin > self.fin_journee)
            overflow_reason = plage.overflow_reason
            if nouvelle_fin > self.fin_journee and not plage.overflow:
                if plage.est_flexible:
                    overflow_reason = "flexible_fit_last_slot"
                else:
                    overflow_reason = "pause_shift_exceeds_window"
                print(f"[WARNING] Task '{plage.nom}' would exceed fin_journee ({self.fin_journee}), marked as overflow: {overflow_reason}")
            
            plage_decalee = PlageResolue(
                id=plage.id,
                nom=plage.nom,
                debut=plage.debut + decalage_total,
                fin=nouvelle_fin,
                priorite=plage.priorite,
                est_flexible=plage.est_flexible,
                est_pause=plage.est_pause,
                overflow=overflow,
                overflow_reason=overflow_reason,
            )
            resultat.append(plage_decalee)
        
        # Insérer les pauses restantes à la fin
        while pause_idx < len(pauses_a_inserer):
            _, pause_id = pauses_a_inserer[pause_idx]
            debut_pause = resultat[-1].fin
            fin_pause = debut_pause + self.duree_pause
            # Skip pause if it would exceed fin_journee (optional pauses)
            if fin_pause > self.fin_journee:
                print(f"[DEBUG] Pause skipped at end (would exceed fin_journee)")
                pause_idx += 1
                continue
            
            pause = PlageResolue(
                id=pause_id,
                nom=NOM_PAUSE,
                debut=debut_pause,
                fin=fin_pause,
                priorite=PRIORITE_PAUSE,
                est_flexible=True,
                est_pause=True,
                overflow=False,
                overflow_reason="",
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
                    overflow=plage.overflow,
                    overflow_reason=plage.overflow_reason,
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
                    overflow=plage.overflow,
                    overflow_reason=plage.overflow_reason,
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
