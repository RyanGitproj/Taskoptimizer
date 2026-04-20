import requests
import json

r = requests.post('http://localhost:8000/api/optimiser', json={
    'activites': [
        {'nom': 'Revue de code', 'duree': 90, 'priorite': 5, 'flexibilite': 'flexible'},
        {'nom': 'Réunion d\'équipe', 'duree': 60, 'priorite': 4, 'flexibilite': 'flexible'},
        {'nom': 'Développement feature', 'duree': 120, 'priorite': 5, 'flexibilite': 'fixe', 'heure_debut_souhaitee': '09:00'},
        {'nom': 'Documentation', 'duree': 45, 'priorite': 2, 'flexibilite': 'flexible'},
        {'nom': 'Veille technologique', 'duree': 30, 'priorite': 3, 'flexibilite': 'flexible'}
    ],
    'heure_debut_travail': '09:00',
    'heure_fin_travail': '18:00',
    'mode_placement': 'intelligent'
})

print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
