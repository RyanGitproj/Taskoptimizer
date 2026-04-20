"""
Module api.routes
-----------------
Définition des routes FastAPI.
Responsabilité unique : validation des entrées HTTP et délégation au service.
Aucune logique métier ou algorithme ici.
"""

import logging
from fastapi import APIRouter, Request, Depends
from fastapi import status
from pydantic import BaseModel
from typing import List

from models.schemas import ParametresOptimisation, ResultatOptimisation, ReponseStandard
from models.exceptions import ErreurMetier
from services.optimisation import optimiser_planning

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Optimisation"])


async def log_raw_body(request: Request):
    body = await request.body()
    body_str = body.decode('utf-8')
    print(f"[RAW BODY DEBUG] CONTENT: {body_str}")
    # Extract heure_fin_travail value
    try:
        import json
        body_json = json.loads(body_str)
        val = body_json.get('heure_fin_travail')
        if val is None:
            print(f"[RAW BODY DEBUG] heure_fin_travail est ABSENT ou NULL dans le JSON brut")
        else:
            print(f"[RAW BODY DEBUG] heure_fin_travail trouvé dans JSON brut: '{val}'")
    except Exception as e:
        print(f"[RAW BODY DEBUG] Erreur lors du parsing JSON: {str(e)}")

@router.post(
    "/optimiser",
    response_model=ReponseStandard[ResultatOptimisation],
    status_code=status.HTTP_200_OK,
    summary="Optimiser le planning journalier",
    description=(
        "Reçoit une liste d'activités avec leurs contraintes et génère "
        "un planning optimisé en utilisant la programmation par contraintes (OR-Tools CP-SAT)."
    ),
    dependencies=[Depends(log_raw_body)],
)
def optimiser(params: ParametresOptimisation) -> ReponseStandard[ResultatOptimisation]:
    """
    POST /api/optimiser

    Body: ParametresOptimisation
    Returns: ReponseStandard[ResultatOptimisation]
    """
    import time
    request_id = int(time.time() * 1000) + int(hash(str(params)) % 10000)
    
    logger.info(f"=== DEMANDE D'OPTIMISATION [REQ-{request_id}] ===")
    logger.info(f"Raw request body type: {type(params)}")
    logger.info(f"Heure debut travail: {params.heure_debut_travail}")
    logger.info(f"Heure fin travail: {params.heure_fin_travail} [REÇUE]")
    logger.info(f"Duree pause: {params.duree_pause} min")
    logger.info(f"Nombre d'activites: {len(params.activites)}")
    for i, act in enumerate(params.activites):
        logger.info(f"  {i+1}. {act.nom} - duree: {act.duree}min, priorite: {act.priorite}, flexibilite: {act.flexibilite}")
        if act.heure_debut_souhaitee:
            logger.info(f"     heure debut souhaitee: {act.heure_debut_souhaitee}")
    logger.info(f"=============================")
    
    resultat = optimiser_planning(params)
    logger.info(f"Optimisation réussie - Score: {resultat.score_optimisation}")
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
