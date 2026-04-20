from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Generic, TypeVar
from enum import Enum

T = TypeVar('T')


class Flexibilite(str, Enum):
    fixe = "fixe"
    flexible = "flexible"


class Activite(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100, description="Nom de l'activité")
    duree: int = Field(..., gt=0, le=480, description="Durée en minutes")
    priorite: int = Field(..., ge=1, le=5, description="Priorité de 1 (basse) à 5 (haute)")
    flexibilite: Flexibilite = Field(..., description="fixe ou flexible")
    heure_debut_souhaitee: str | None = Field(
        None,
        description="Heure de début souhaitée pour les activités fixes (format HH:MM)"
    )

    @field_validator("heure_debut_souhaitee")
    @classmethod
    def valider_format_heure(cls, v):
        if v is None:
            return v
        try:
            heure, minute = v.split(":")
            assert 0 <= int(heure) <= 23
            assert 0 <= int(minute) <= 59
        except (ValueError, AssertionError):
            raise ValueError("Format d'heure invalide. Utilisez HH:MM")
        return v


class ParametresOptimisation(BaseModel):
    activites: List[Activite] = Field(..., min_length=1, max_length=20)
    heure_debut_travail: str = Field(..., description="Début de journée (HH:MM)")
    heure_fin_travail: str = Field(..., description="Fin de journée (HH:MM)")
    duree_pause: int = Field(default=15, ge=0, le=60, description="Durée des pauses en minutes")

    @field_validator("heure_fin_travail")
    @classmethod
    def log_heure_fin_travail(cls, v):
        print(f"[SCHEMA DEBUG] heure_fin_travail reçue dans schema: '{v}'")
        return v

    @field_validator("heure_debut_travail", "heure_fin_travail")
    @classmethod
    def valider_heure_travail(cls, v):
        try:
            heure, minute = v.split(":")
            assert 0 <= int(heure) <= 23
            assert 0 <= int(minute) <= 59
        except (ValueError, AssertionError):
            raise ValueError("Format d'heure invalide. Utilisez HH:MM")
        return v


class PlageHoraire(BaseModel):
    activite: str
    debut: str
    fin: str
    priorite: int
    flexibilite: str
    est_pause: bool = False
    overflow: bool = False
    overflow_reason: str = ""


class ResultatOptimisation(BaseModel):
    planning: List[PlageHoraire]
    score_optimisation: float = Field(..., description="Score de satisfaction des priorités (0–100)")
    temps_total_planifie: int = Field(..., description="Temps total planifié en minutes")
    activites_non_planifiees: List[str] = Field(
        default_factory=list,
        description="Activités qui n'ont pas pu être planifiées"
    )
    message: str = Field(default="Optimisation réussie")


# ---------------------------------------------------------------------------
# Format standard de réponse API
# ---------------------------------------------------------------------------

class ErreurDetail(BaseModel):
    code: str = Field(..., description="Code d'erreur normalisé")
    message: str = Field(..., description="Description claire de l'erreur")


class ReponseStandard(BaseModel, Generic[T]):
    success: bool = Field(..., description="Indique si la requête a réussi")
    data: T | None = Field(None, description="Données de la réponse si succès")
    error: ErreurDetail | None = Field(None, description="Détail de l'erreur si échec")
