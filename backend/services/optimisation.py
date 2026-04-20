"""
Module services.optimisation
-----------------------------
Couche service : orchestre la conversion des données API vers le solveur
et reformate les résultats pour la couche API.
Aucune logique OR-Tools ici — uniquement de l'orchestration.
"""

import logging
from typing import List
from models.schemas import (
    Activite,
    Flexibilite,
    ParametresOptimisation,
    PlageHoraire,
    ResultatOptimisation,
)
from models.exceptions import ErreurMetier, ErreurHorairesInvalides, ErreurSolveur
from solver.engine import MoteurOptimisation, TacheEntree

logger = logging.getLogger(__name__)


def _heure_en_minutes(heure: str) -> int:
    """Convertit 'HH:MM' en nombre de minutes depuis minuit."""
    h, m = heure.split(":")
    return int(h) * 60 + int(m)


def _minutes_en_heure(minutes: int) -> str:
    """Convertit un nombre de minutes depuis minuit en 'HH:MM'."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def _convertir_activites(activites: List[Activite]) -> List[TacheEntree]:
    """Transforme les schémas Pydantic en structures internes du solveur."""
    taches = []
    for i, act in enumerate(activites):
        debut_souhaite = None
        if act.flexibilite == Flexibilite.fixe and act.heure_debut_souhaitee:
            debut_souhaite = _heure_en_minutes(act.heure_debut_souhaitee)

        taches.append(TacheEntree(
            id=i,
            nom=act.nom,
            duree=act.duree,
            priorite=act.priorite,
            est_flexible=(act.flexibilite == Flexibilite.flexible),
            debut_souhaite=debut_souhaite,
        ))
    return taches


def _convertir_planning(plages_resolues) -> List[PlageHoraire]:
    """Transforme les résultats internes en schémas de réponse API."""
    return [
        PlageHoraire(
            activite=p.nom,
            debut=_minutes_en_heure(p.debut),
            fin=_minutes_en_heure(p.fin),
            priorite=p.priorite,
            flexibilite="flexible" if p.est_flexible else "fixe",
            overflow=p.overflow,
            overflow_reason=p.overflow_reason,
        )
        for p in plages_resolues
    ]


def optimiser_planning(params: ParametresOptimisation) -> ResultatOptimisation:
    """
    Point d'entrée unique du service d'optimisation.
    Orchestre la conversion, l'appel au solveur et le formatage de la réponse.
    """
    logger.info(f"Début optimisation - {len(params.activites)} activités")

    debut_journee = _heure_en_minutes(params.heure_debut_travail)
    fin_journee = _heure_en_minutes(params.heure_fin_travail)

    if debut_journee >= fin_journee:
        logger.warning(f"Créneaux horaires invalides: début={params.heure_debut_travail}, fin={params.heure_fin_travail}")
        raise ErreurHorairesInvalides(
            debut=params.heure_debut_travail,
            fin=params.heure_fin_travail,
        )

    # Vérifier les conflits entre tâches fixes
    fixes = [a for a in params.activites if a.flexibilite == Flexibilite.fixe and a.heure_debut_souhaitee]
    if len(fixes) > 1:
        for i in range(len(fixes)):
            for j in range(i + 1, len(fixes)):
                t1_debut = _heure_en_minutes(fixes[i].heure_debut_souhaitee)
                t1_fin = t1_debut + fixes[i].duree
                t2_debut = _heure_en_minutes(fixes[j].heure_debut_souhaitee)
                t2_fin = t2_debut + fixes[j].duree
                # Vérifier le chevauchement
                if not (t1_fin <= t2_debut or t2_fin <= t1_debut):
                    logger.error(f"Conflit entre tâches fixes: {fixes[i].nom} et {fixes[j].nom}")
                    raise ErreurMetier(
                        code="CONFLIT_TACHES_FIXES",
                        message=f"Les tâches fixes '{fixes[i].nom}' et '{fixes[j].nom}' se chevauchent."
                    )

    taches = _convertir_activites(params.activites)
    logger.debug(f"Conversion réussie: {len(taches)} tâches pour le solveur")

    try:
        moteur = MoteurOptimisation(
            debut_journee=debut_journee,
            fin_journee=fin_journee,
            mode_placement=params.mode_placement,
        )

        resultat = moteur.resoudre(taches)
    except ErreurMetier:
        raise
    except Exception as exc:
        logger.error(f"Erreur du solveur: {exc}", exc_info=True)
        raise ErreurSolveur(detail=str(exc)) from exc

    logger.debug(f"Solveur terminé - {len(resultat.planifiees)} planifiées, {len(resultat.non_planifiees)} non planifiées")

    planning = _convertir_planning(resultat.planifiees)

    temps_total = sum(
        _heure_en_minutes(p.fin) - _heure_en_minutes(p.debut)
        for p in planning
    )

    message = "Optimisation réussie."
    if resultat.non_planifiees:
        noms = ", ".join(resultat.non_planifiees)
        message = f"Optimisation partielle. Activités non planifiées : {noms}."

    return ResultatOptimisation(
        planning=planning,
        score_optimisation=resultat.score,
        temps_total_planifie=temps_total,
        activites_non_planifiees=resultat.non_planifiees,
        message=message,
    )
