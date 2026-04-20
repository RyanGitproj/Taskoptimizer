"""
Module solver.engine
--------------------
Moteur d'optimisation basé sur Google OR-Tools (CP-SAT).
Responsabilité unique : transformer des activités en un planning optimisé.
"""

from dataclasses import dataclass
from typing import List, Optional

from ortools.sat.python import cp_model


@dataclass(frozen=True)
class TacheEntree:
    id: int
    nom: str
    duree: int
    priorite: int
    est_flexible: bool
    debut_souhaite: Optional[int] = None


@dataclass(frozen=True)
class PlageResolue:
    id: int
    nom: str
    debut: int
    fin: int
    priorite: int
    est_flexible: bool
    overflow: bool = False
    overflow_reason: str = ""


@dataclass(frozen=True)
class ResultatSolveur:
    planifiees: List[PlageResolue]
    non_planifiees: List[str]
    score: float


POIDS_PRIORITE = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}

# Objectif scalarisé (entiers uniquement)
# On utilise des échelles très différentes pour garantir la hiérarchie des objectifs
GAIN_BASE_PAR_TACHE = 1_000_000  # Priorité absolue : planifier les tâches
PENALITE_MAKESPAN = 100
MODE_COMPACT = "compact"
MODE_UNIFORME = "uniforme"
MODE_INTELLIGENT = "intelligent"


class MoteurOptimisation:
    """
    Encapsule la logique OR-Tools.
    Le solveur:
    - maximise les tâches planifiées (priorité dominante),
    - compacte les tâches vers la gauche (minimise les trous inutiles),
    - respecte strictement les contraintes de fenêtre, non-chevauchement et ancrage.
    """

    def __init__(
        self,
        debut_journee: int,
        fin_journee: int,
        mode_placement: str = MODE_INTELLIGENT,
    ):
        self.debut_journee = debut_journee
        self.fin_journee = fin_journee
        self.mode_placement = mode_placement

    def resoudre(self, taches: List[TacheEntree]) -> ResultatSolveur:
        modele = cp_model.CpModel()
        horizon = self.fin_journee

        vars_taches = self._creer_variables(modele, taches, horizon)

        self._contrainte_pas_chevauchement(modele, vars_taches)
        self._contrainte_fenetre_travail(modele, vars_taches)
        self._contrainte_ancrage_fixe(modele, taches, vars_taches)
        self._contrainte_symmetry_breaking(modele, taches, vars_taches)
        
        self._definir_objectif(modele, taches, vars_taches)
        self._configurer_strategie_decision(modele, vars_taches)

        solveur = cp_model.CpSolver()
        solveur.parameters.max_time_in_seconds = 25.0
        solveur.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
        solveur.parameters.cp_model_presolve = True
        solveur.parameters.linearization_level = 1
        solveur.parameters.num_search_workers = 4
        statut = solveur.Solve(modele)

        return self._extraire_resultat(solveur, statut, taches, vars_taches)

    def _contrainte_symmetry_breaking(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ) -> None:
        """
        Évite que le solveur n'explore des permutations inutiles de tâches identiques.
        """
        par_signature = {}
        for i, tache in enumerate(taches):
            # Signature: même nom, durée, priorité, flexibilité
            sig = (tache.nom, tache.duree, tache.priorite, tache.est_flexible)
            par_signature.setdefault(sig, []).append(i)
        
        for indices in par_signature.values():
            for k in range(len(indices) - 1):
                idx1, idx2 = indices[k], indices[k+1]
                # Si les deux sont planifiées, l'ordre doit être conservé
                modele.Add(vars_taches[idx1]["debut"] <= vars_taches[idx2]["debut"])

    def _configurer_strategie_decision(
        self, modele: cp_model.CpModel, vars_taches: List[dict]
    ) -> None:
        """
        Guide le solveur pour explorer d'abord les variables les plus critiques.
        """
        # On branche d'abord sur la planification (oui/non)
        all_planifiee = [v["planifiee"] for v in vars_taches]
        modele.AddDecisionStrategy(
            all_planifiee, 
            cp_model.CHOOSE_FIRST, 
            cp_model.SELECT_MAX_VALUE
        )

        # On branche sur les débuts. 
        # Pour Compact: on veut le plus tôt possible.
        # Pour les autres: on laisse le solveur explorer pour trouver l'optimum d'étalement.
        all_debut = [v["debut"] for v in vars_taches]
        if self.mode_placement == MODE_COMPACT:
            modele.AddDecisionStrategy(
                all_debut,
                cp_model.CHOOSE_LOWEST_MIN,
                cp_model.SELECT_MIN_VALUE
            )
        else:
            # On ne force pas de direction pour laisser l'objectif d'étalement agir
            pass

    def _creer_variables(
        self, modele: cp_model.CpModel, taches: List[TacheEntree], horizon: int
    ) -> List[dict]:
        vars_liste = []
        for tache in taches:
            # Réduction des domaines: une tâche ne peut pas finir après l'horizon
            # et ne peut pas commencer avant le début de journée.
            debut = modele.NewIntVar(self.debut_journee, horizon - tache.duree, f"debut_{tache.id}")
            fin = modele.NewIntVar(self.debut_journee + tache.duree, horizon, f"fin_{tache.id}")
            planifiee = modele.NewBoolVar(f"planifiee_{tache.id}")
            intervalle = modele.NewOptionalIntervalVar(
                debut, tache.duree, fin, planifiee, f"intervalle_{tache.id}"
            )
            vars_liste.append(
                {
                    "debut": debut,
                    "fin": fin,
                    "planifiee": planifiee,
                    "intervalle": intervalle,
                }
            )
        return vars_liste

    def _contrainte_pas_chevauchement(
        self, modele: cp_model.CpModel, vars_taches: List[dict]
    ) -> None:
        modele.AddNoOverlap([v["intervalle"] for v in vars_taches])

    def _contrainte_fenetre_travail(
        self, modele: cp_model.CpModel, vars_taches: List[dict]
    ) -> None:
        for v in vars_taches:
            modele.Add(v["debut"] >= self.debut_journee).OnlyEnforceIf(v["planifiee"])
            modele.Add(v["fin"] <= self.fin_journee).OnlyEnforceIf(v["planifiee"])

    def _contrainte_ancrage_fixe(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ) -> None:
        for i, tache in enumerate(taches):
            if not tache.est_flexible and tache.debut_souhaite is not None:
                # Une tâche fixe est une contrainte forte: si son heure est fournie,
                # elle doit être planifiée exactement à cette heure.
                modele.Add(vars_taches[i]["planifiee"] == 1)
                modele.Add(vars_taches[i]["debut"] == tache.debut_souhaite).OnlyEnforceIf(
                    vars_taches[i]["planifiee"]
                )

    def _definir_objectif(
        self,
        modele: cp_model.CpModel,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ) -> None:
        termes = []
        fenetre = self.fin_journee - self.debut_journee
        nb_taches = len(taches)

        # 1. Gain principal: Planifier le plus de tâches possible selon priorité
        for i, tache in enumerate(taches):
            poids_priorite = POIDS_PRIORITE.get(tache.priorite, tache.priorite)
            gain = poids_priorite * GAIN_BASE_PAR_TACHE
            termes.append(gain * vars_taches[i]["planifiee"])

        # 2. Gestion de l'Étagement et de la Respiration
        if self.mode_placement != MODE_COMPACT and nb_taches > 0:
            # Bonus d'ordre (Soft constraint)
            for i in range(nb_taches - 1):
                ordre_ok = modele.NewBoolVar(f"ordre_{i}_{i+1}")
                modele.Add(vars_taches[i]["fin"] <= vars_taches[i+1]["debut"]).OnlyEnforceIf(ordre_ok)
                termes.append(10000 * ordre_ok)

                # Calcul de l'espace REEL (slack)
                slack = modele.NewIntVar(0, fenetre, f"slack_{i}")
                # Si l'ordre est respecté, slack = debut_next - fin_prev
                modele.Add(slack == vars_taches[i+1]["debut"] - vars_taches[i]["fin"]).OnlyEnforceIf(ordre_ok)
                # SI L'ORDRE N'EST PAS RESPECTÉ, LE SLACK EST DE 0 (Crucial pour éviter les bonus gratuits)
                modele.Add(slack == 0).OnlyEnforceIf(ordre_ok.Not())

                # Récompense de respiration par paliers (Concave Reward)
                # Palier 1 : 0-20 min (Vital)
                s1 = modele.NewIntVar(0, 20, f"s1_{i}")
                modele.AddMinEquality(s1, [slack, 20])
                termes.append(5000 * s1)
                
                # Palier 2 : 20-60 min (Confortable)
                s2 = modele.NewIntVar(0, 40, f"s2_{i}")
                modele.Add(s2 == slack - s1)
                s2_capped = modele.NewIntVar(0, 40, f"s2c_{i}")
                modele.AddMinEquality(s2_capped, [s2, 40])
                termes.append(2000 * s2_capped)

                # PÉNALITÉ DE TEMPS MORT : Si slack > 90 min, on pénalise lourdement
                # Cela force le solveur à redistribuer les grands vides
                is_waste = modele.NewBoolVar(f"waste_{i}")
                modele.Add(slack > 90).OnlyEnforceIf(is_waste)
                modele.Add(slack <= 90).OnlyEnforceIf(is_waste.Not())
                termes.append(-15000 * is_waste)

            # 3. Gestion de la Fin de Journée
            makespan = modele.NewIntVar(self.debut_journee, self.fin_journee, "makespan")
            for i in range(nb_taches):
                modele.Add(makespan >= vars_taches[i]["fin"]).OnlyEnforceIf(vars_taches[i]["planifiee"])
            
            # En mode intelligent/uniforme, on réduit drastiquement la pression de fin 
            # pour laisser l'étalement respirer.
            termes.append(-50 * (makespan - self.debut_journee))

            if self.mode_placement == MODE_INTELLIGENT:
                for i, tache in enumerate(taches):
                    if tache.est_flexible:
                        p = POIDS_PRIORITE.get(tache.priorite, 3)
                        if p >= 4:
                            # Attraction vers le matin pour les P5/P4
                            termes.append(-(p * 100) * vars_taches[i]["debut"])

        elif self.mode_placement == MODE_COMPACT:
            # COMPACT : Minimiser le temps de fin total
            makespan = modele.NewIntVar(self.debut_journee, self.fin_journee, "makespan")
            for i in range(nb_taches):
                modele.Add(makespan >= vars_taches[i]["fin"]).OnlyEnforceIf(vars_taches[i]["planifiee"])
            termes.append(-PENALITE_MAKESPAN * (makespan - self.debut_journee))

        modele.Maximize(sum(termes))

    def _extraire_resultat(
        self,
        solveur: cp_model.CpSolver,
        statut: int,
        taches: List[TacheEntree],
        vars_taches: List[dict],
    ) -> ResultatSolveur:
        if statut not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return ResultatSolveur(
                planifiees=[],
                non_planifiees=[t.nom for t in taches],
                score=0.0,
            )

        planifiees: List[PlageResolue] = []
        non_planifiees: List[str] = []
        score_total = 0.0
        score_max = sum(POIDS_PRIORITE.get(tache.priorite, tache.priorite) for tache in taches)

        for i, tache in enumerate(taches):
            if solveur.Value(vars_taches[i]["planifiee"]):
                debut = int(solveur.Value(vars_taches[i]["debut"]))
                fin = int(solveur.Value(vars_taches[i]["fin"]))
                planifiees.append(
                    PlageResolue(
                        id=tache.id,
                        nom=tache.nom,
                        debut=debut,
                        fin=fin,
                        priorite=tache.priorite,
                        est_flexible=tache.est_flexible,
                    )
                )
                score_total += POIDS_PRIORITE.get(tache.priorite, tache.priorite)
            else:
                non_planifiees.append(tache.nom)

        planifiees.sort(key=lambda p: (p.debut, p.fin))

        # PLUS DE POST-PROCESSING PYTHON ICI ! 
        # L'étalage est géré par la fonction objectif.

        score_pct = round((score_total / score_max) * 100, 1) if score_max > 0 else 0.0
        return ResultatSolveur(planifiees=planifiees, non_planifiees=non_planifiees, score=score_pct)
