"""Script de test pour vérifier que les pauses sont optionnelles."""
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
print("TEST: Les pauses doivent être optionnelles")
print("=" * 60)

# Test avec un planning très chargé - les pauses devraient être sautées
code, body = fetch("/api/optimiser", {
    "activites": [
        {"nom": "Tâche 1", "duree": 120, "priorite": 5, "flexibilite": "flexible"},
        {"nom": "Tâche 2", "duree": 120, "priorite": 5, "flexibilite": "flexible"},
        {"nom": "Tâche 3", "duree": 120, "priorite": 5, "flexibilite": "flexible"},
        {"nom": "Tâche 4", "duree": 120, "priorite": 5, "flexibilite": "flexible"},
    ],
    "heure_debut_travail": "09:00",
    "heure_fin_travail": "18:00",
    "duree_pause": 15,
})

print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))

planning = body["data"]["planning"]
pauses = [p for p in planning if p["est_pause"]]

print(f"\n✅ Planning généré avec {len(pauses)} pause(s)")

# Vérifier qu'il n'y a pas d'overflow
overflow_tasks = [p for p in planning if p.get("overflow", False)]
if len(overflow_tasks) == 0:
    print("✅ TEST PASSE: Aucun overflow malgré planning chargé")
else:
    print(f"❌ TEST ÉCHOUÉ: {len(overflow_tasks)} tâches en overflow")
    for task in overflow_tasks:
        print(f"   {task['activite']}: {task['overflow_reason']}")

# Vérifier que les pauses n'ont pas causé de dépassement
if len(pauses) > 0:
    print(f"⚠️  {len(pauses)} pause(s) insérée(s)")
    for pause in pauses:
        print(f"   Pause: {pause['debut']} → {pause['fin']}")
