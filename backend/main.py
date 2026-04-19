"""
main.py — Point d'entrée de l'application TaskOptimizer Backend
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.routes import router
from models.exceptions import ErreurMetier

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TaskOptimizer — Moteur de Planification par Contraintes",
    description=(
        "API REST exposant un moteur d'optimisation basé sur Google OR-Tools (CP-SAT). "
        "Génère automatiquement un planning journalier optimisé à partir d'une liste d'activités."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS : autoriser le frontend Next.js en développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# ---------------------------------------------------------------------------
# Gestionnaires d'exceptions — Format standard de réponse
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Erreurs de validation Pydantic (422) → format standard."""
    erreurs = []
    for err in exc.errors():
        champ = " → ".join(str(loc) for loc in err.get("loc", []))
        erreurs.append(f"{champ}: {err.get('msg', 'valeur invalide')}")
    message = "; ".join(erreurs)
    logger.warning(f"Erreur de validation: {message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
            },
        },
    )


@app.exception_handler(ErreurMetier)
async def business_exception_handler(request: Request, exc: ErreurMetier):
    """Erreurs métier (400) → format standard."""
    logger.warning(f"Erreur métier [{exc.code}]: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Erreurs internes non gérées (500) → format standard."""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Erreur interne du serveur. Veuillez réessayer.",
            },
        },
    )


@app.get("/", include_in_schema=False)
def racine():
    return {
        "success": True,
        "data": {
            "application": "TaskOptimizer",
            "version": "1.0.0",
            "documentation": "/docs",
        },
        "error": None,
    }
