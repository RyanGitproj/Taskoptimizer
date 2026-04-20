import unittest

from models.schemas import Activite, Flexibilite, ParametresOptimisation
from models.exceptions import ErreurTacheFixeHorsFenetre
from services.optimisation import optimiser_planning


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class TestSolverRegression(unittest.TestCase):
    def test_charge_complete_sans_trou_inutile(self):
        """Si la somme des tâches remplit la fenêtre, le planning couvre toute la journée."""
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Deep Work", duree=180, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Projet", duree=180, priorite=4, flexibilite=Flexibilite.flexible),
                Activite(nom="Admin", duree=180, priorite=3, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        taches = resultat.planning

        self.assertGreaterEqual(len(taches), 3)
        self.assertEqual(taches[0].debut, "09:00")
        self.assertEqual(taches[-1].fin, "18:00")

        # Vérifie aucun trou entre tâches planifiées.
        for i in range(len(taches) - 1):
            self.assertEqual(taches[i].fin, taches[i + 1].debut)

    def test_ancrage_tache_fixe_et_pas_de_chevauchement(self):
        params = ParametresOptimisation(
            activites=[
                Activite(
                    nom="Réunion client",
                    duree=60,
                    priorite=5,
                    flexibilite=Flexibilite.fixe,
                    heure_debut_souhaitee="14:00",
                ),
                Activite(nom="Rédaction", duree=150, priorite=4, flexibilite=Flexibilite.flexible),
                Activite(nom="Analyse", duree=120, priorite=3, flexibilite=Flexibilite.flexible),
                Activite(nom="Revue", duree=90, priorite=3, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        planning = resultat.planning

        reunion = next(p for p in planning if p.activite == "Réunion client")
        self.assertEqual(reunion.debut, "14:00")
        self.assertEqual(reunion.fin, "15:00")

        # Vérifie absence de chevauchement global.
        plages = sorted(planning, key=lambda p: _to_minutes(p.debut))
        for i in range(len(plages) - 1):
            fin_courante = _to_minutes(plages[i].fin)
            debut_suivante = _to_minutes(plages[i + 1].debut)
            self.assertLessEqual(fin_courante, debut_suivante)

    def test_tache_longue_non_divisee(self):
        """Une tâche de 120 min reste une seule tâche (pas de '(partie 1/2)')."""
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Développement feature", duree=120, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Revue", duree=60, priorite=4, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        activites = [p.activite for p in resultat.planning]
        self.assertIn("Développement feature", activites)
        self.assertFalse(any("(partie" in nom for nom in activites))

    def test_etalement_reduit_blanc_final_sur_flexibles(self):
        """Quand la charge est plus faible que la journée, le blanc final est étalé."""
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Revue de code", duree=90, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Veille technologique", duree=30, priorite=3, flexibilite=Flexibilite.flexible),
                Activite(nom="Réunion d'équipe", duree=60, priorite=4, flexibilite=Flexibilite.flexible),
                Activite(nom="Documentation", duree=45, priorite=2, flexibilite=Flexibilite.flexible),
                Activite(nom="Développement feature", duree=120, priorite=5, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        taches = resultat.planning
        fin_derniere = _to_minutes(taches[-1].fin)
        debut_journee = _to_minutes("09:00")
        fin_journee = _to_minutes("18:00")

        # Le modèle d'étalement doit éviter un énorme blanc final (3h15 auparavant).
        self.assertGreaterEqual(fin_derniere, _to_minutes("17:25"))
        self.assertLessEqual(fin_journee - fin_derniere, 35)

        # Le temps total de travail est conservé.
        temps_total = sum(_to_minutes(p.fin) - _to_minutes(p.debut) for p in taches)
        self.assertEqual(temps_total, 345)
        self.assertGreaterEqual(_to_minutes(taches[0].debut), debut_journee)

    def test_tache_critique_ajoutee_est_planifiee_si_capacite_disponible(self):
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Revue de code", duree=90, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Veille technologique", duree=30, priorite=3, flexibilite=Flexibilite.flexible),
                Activite(nom="Réunion d'équipe", duree=60, priorite=4, flexibilite=Flexibilite.flexible),
                Activite(nom="Documentation", duree=45, priorite=2, flexibilite=Flexibilite.flexible),
                Activite(nom="Développement feature", duree=120, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Incident critique", duree=60, priorite=5, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        activites = [p.activite for p in resultat.planning]
        self.assertIn("Incident critique", activites)
        self.assertNotIn("Incident critique", resultat.activites_non_planifiees)

    def test_etalement_favorise_priorites_hautes_plus_tot(self):
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Tache basse", duree=60, priorite=2, flexibilite=Flexibilite.flexible),
                Activite(nom="Tache critique", duree=60, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Tache moyenne", duree=60, priorite=3, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
        )

        resultat = optimiser_planning(params)
        taches = resultat.planning
        debuts = {p.activite: _to_minutes(p.debut) for p in taches}

        self.assertLessEqual(debuts["Tache critique"], debuts["Tache moyenne"])
        self.assertLessEqual(debuts["Tache critique"], debuts["Tache basse"])

    def test_mode_compact_termine_plus_tot_sur_charge_legere(self):
        params = ParametresOptimisation(
            activites=[
                Activite(nom="Revue de code", duree=90, priorite=5, flexibilite=Flexibilite.flexible),
                Activite(nom="Veille technologique", duree=30, priorite=3, flexibilite=Flexibilite.flexible),
                Activite(nom="Réunion d'équipe", duree=60, priorite=4, flexibilite=Flexibilite.flexible),
                Activite(nom="Documentation", duree=45, priorite=2, flexibilite=Flexibilite.flexible),
                Activite(nom="Développement feature", duree=120, priorite=5, flexibilite=Flexibilite.flexible),
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
            mode_placement="compact",
        )

        resultat = optimiser_planning(params)
        taches = resultat.planning
        self.assertEqual(taches[0].debut, "09:00")
        self.assertLessEqual(_to_minutes(taches[-1].fin), _to_minutes("15:00"))

    def test_tache_fixe_hors_fenetre_declenche_erreur_metier(self):
        params = ParametresOptimisation(
            activites=[
                Activite(
                    nom="Réunion tardive",
                    duree=90,
                    priorite=5,
                    flexibilite=Flexibilite.fixe,
                    heure_debut_souhaitee="17:00",
                )
            ],
            heure_debut_travail="09:00",
            heure_fin_travail="18:00",
            mode_placement="intelligent",
        )

        with self.assertRaises(ErreurTacheFixeHorsFenetre):
            optimiser_planning(params)


if __name__ == "__main__":
    unittest.main()
