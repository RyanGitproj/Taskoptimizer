"""Script de test pour vérifier le placement des tâches flexibles."""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"


def fetch(path, data=None):
    if data:
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
    else:
        req = urllib.request.Request(f"{BASE}{path}")
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


print("=" * 60)
print("TEST: Tâches flexibles doivent être placées tôt, pas en fin")
print("=" * 60)

# Test avec une tâche flexible et une tâche fixe
code, body = fetch("/api/optimiser", {
    "activites": [
        {"nom": "Réunion fixe", "duree": 60, "priorite": 5, "flexibilite": "fixe", "heure_debut_souhaitee": "14:00"},
        {"nom": "Tâche flexible", "duree": 60, "priorite": 3, "flexibilite": "flexible"},
    ],
    "heure_debut_travail": "09:00",
    "heure_fin_travail": "18:00",
    "duree_pause": 15,
})

print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))

# Vérifier que la tâche flexible est placée tôt (pas à la fin)
planning = body["data"]["planning"]
flexible_task = next((t for t in planning if "flexible" in t["activite"].lower()), None)

if flexible_task:
    print(f"\n✅ Tâche flexible trouvée:")
    print(f"   Nom: {flexible_task['activite']}")
    print(f"   Début: {flexible_task['debut']}")
    print(f"   Fin: {flexible_task['fin']}")
    print(f"   Overflow: {flexible_task.get('overflow', False)}")
    
    # Vérifier qu'elle n'est pas en fin de journée (après 17:00)
    debut_minutes = int(flexible_task['debut'].split(':')[0]) * 60 + int(flexible_task['debut'].split(':')[1])
    if debut_minutes < 1020:  # 17:00
        print("✅ TEST PASSE: Tâche flexible placée tôt")
    else:
        print("❌ TEST ÉCHOUÉ: Tâche flexible placée en fin de journée")
else:
    print("❌ TEST ÉCHOUÉ: Tâche flexible non planifiée")
