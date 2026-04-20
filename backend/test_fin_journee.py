"""Script de test pour vérifier la contrainte fin_journee."""
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
print("TEST: Tâches qui dépassent fin_journee doivent être rejetées")
print("=" * 60)

# Test avec une tâche qui dépasse forcément 18:00
code, body = fetch("/api/optimiser", {
    "activites": [
        {"nom": "Tâche très longue", "duree": 300, "priorite": 5, "flexibilite": "flexible"},
        {"nom": "Autre tâche", "duree": 60, "priorite": 3, "flexibilite": "flexible"},
    ],
    "heure_debut_travail": "17:00",
    "heure_fin_travail": "18:00",
})

print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))

# Vérifier que les tâches qui dépassent 18:00 sont non planifiées
assert body["success"] is True
planning = body["data"]["planning"]

# Vérifier qu'aucune tâche ne dépasse 18:00 (1080 minutes)
for tache in planning:
    fin_minutes = int(tache["fin"].split(":")[0]) * 60 + int(tache["fin"].split(":")[1])
    assert fin_minutes <= 1080, f"Tâche {tache['activite']} dépasse 18:00: fin={tache['fin']} ({fin_minutes} min)"

print("\n✅ TEST PASSE: Aucune tâche ne dépasse 18:00")
