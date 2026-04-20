"""
Module api.routes
-----------------
Définition des routes FastAPI.
Responsabilité unique : validation des entrées HTTP et délégation au service.
Aucune logique métier ou algorithme ici.
"""

import logging
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List

from models.schemas import ParametresOptimisation, ResultatOptimisation, ReponseStandard
from models.exceptions import ErreurMetier
from services.optimisation import optimiser_planning

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Optimisation"])

@router.post(
    "/optimiser",
    response_model=ReponseStandard[ResultatOptimisation],
    status_code=status.HTTP_200_OK,
    summary="Optimiser le planning journalier",
    description=(
        "Reçoit une liste d'activités avec leurs contraintes et génère "
        "un planning optimisé en utilisant la programmation par contraintes (OR-Tools CP-SAT)."
    ),
)
def optimiser(params: ParametresOptimisation) -> ReponseStandard[ResultatOptimisation]:
    """
    POST /api/optimiser

    Body: ParametresOptimisation
    Returns: ReponseStandard[ResultatOptimisation]
    """
    logger.info(f"Optimisation demandée - {len(params.activites)} activités")
    
    resultat = optimiser_planning(params)
    logger.info(f"Optimisation réussie - Score: {resultat.score_optimisation}%")
    return ReponseStandard(success=True, data=resultat, error=None)


@router.get(
    "/sante",
    status_code=status.HTTP_200_OK,
    summary="Vérification de l'état du service",
)
def sante() -> ReponseStandard[dict]:
    return ReponseStandard(
        success=True,
        data={"statut": "opérationnel", "service": "TaskOptimizer"},
        error=None,
    )
