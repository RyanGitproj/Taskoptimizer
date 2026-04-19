"""
Module models.exceptions
------------------------
Exceptions métier personnalisées.
Chaque exception porte un code d'erreur normalisé et un message clair.
"""


class ErreurMetier(Exception):
    """Exception de base pour les erreurs métier."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ErreurHorairesInvalides(ErreurMetier):
    """L'heure de début est postérieure ou égale à l'heure de fin."""

    def __init__(self, debut: str, fin: str):
        super().__init__(
            code="HORAIRES_INVALIDES",
            message=f"L'heure de début ({debut}) doit être antérieure à l'heure de fin ({fin}).",
        )


class ErreurSolveur(ErreurMetier):
    """Erreur interne du solveur OR-Tools."""

    def __init__(self, detail: str):
        super().__init__(
            code="ERREUR_SOLVEUR",
            message=f"Erreur interne du solveur : {detail}",
        )
