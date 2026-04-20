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


class ErreurTacheFixeHorsFenetre(ErreurMetier):
    """Une tâche fixe est positionnée hors fenêtre de travail."""

    def __init__(self, nom_tache: str, debut: str, fin: str):
        super().__init__(
            code="TACHE_FIXE_HORS_FENETRE",
            message=(
                f"La tâche fixe '{nom_tache}' est hors fenêtre de travail "
                f"({debut} - {fin}). Ajustez l'heure souhaitée ou la durée."
            ),
        )
