"""
Test direct backend pour isoler le problème de corruption de heure_fin_travail
"""
import requests
import json

# Backend URL
BASE_URL = "http://localhost:8000"

# Payload HARDCODÉ avec heure_fin_travail = 20:00
payload = {
    "activites": [
        {
            "nom": "Revue de code",
            "duree": 90,
            "priorite": 5,
            "flexibilite": "fixe",
            "heure_debut_souhaitee": "09:00"
        },
        {
            "nom": "Réunion d'équipe",
            "duree": 60,
            "priorite": 4,
            "flexibilite": "fixe",
            "heure_debut_souhaitee": "11:00"
        },
        {
            "nom": "Développement feature",
            "duree": 120,
            "priorite": 5,
            "flexibilite": "flexible"
        }
    ],
    "heure_debut_travail": "09:00",
    "heure_fin_travail": "20:00",  # HARDCODÉ à 20:00
    "duree_pause": 15
}

print("=" * 50)
print("TEST DIRECT BACKEND - SANS FRONTEND")
print("=" * 50)
print(f"Payload envoyé (HARDCODÉ):")
print(json.dumps(payload, indent=2))
print(f"heure_fin_travail dans payload: '{payload['heure_fin_travail']}'")
print("=" * 50)

try:
    response = requests.post(f"{BASE_URL}/api/optimiser", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('data'):
            print(f"Score: {result['data'].get('score_optimisation')}")
            print(f"Planning: {len(result['data'].get('planning', []))} tâches")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    print(f"Backend peut ne pas être démarré. Lance-le avec: cd backend && .venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000")

print("=" * 50)
print("CONCLUSION:")
print("Si backend reçoit 20:00 → problème frontend")
print("Si backend reçoit 18:00 → problème backend ou middleware")
print("=" * 50)
