"""Script de test pour vérifier le format standard des réponses API."""
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
print("TEST 1: GET / (racine)")
code, body = fetch("/")
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is True
assert body["data"] is not None
assert body["error"] is None

print("\n" + "=" * 60)
print("TEST 2: GET /api/sante")
code, body = fetch("/api/sante")
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is True
assert body["data"]["statut"] == "opérationnel"
assert body["error"] is None

print("\n" + "=" * 60)
print("TEST 3: POST /api/optimiser (succès)")
code, body = fetch("/api/optimiser", {
    "activites": [
        {"nom": "Travail", "duree": 120, "priorite": 5, "flexibilite": "fixe", "heure_debut_souhaitee": "09:00"},
        {"nom": "Sport", "duree": 60, "priorite": 3, "flexibilite": "flexible"},
    ],
    "heure_debut_travail": "09:00",
    "heure_fin_travail": "18:00",
    "duree_pause": 15,
})
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is True
assert body["data"]["score_optimisation"] == 100.0
assert body["error"] is None

print("\n" + "=" * 60)
print("TEST 4: POST /api/optimiser (validation error - liste vide)")
code, body = fetch("/api/optimiser", {"activites": []})
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is False
assert body["data"] is None
assert body["error"]["code"] == "VALIDATION_ERROR"

print("\n" + "=" * 60)
print("TEST 5: POST /api/optimiser (business error - horaires invalides)")
code, body = fetch("/api/optimiser", {
    "activites": [{"nom": "Test", "duree": 60, "priorite": 3, "flexibilite": "flexible"}],
    "heure_debut_travail": "18:00",
    "heure_fin_travail": "09:00",
    "duree_pause": 15,
})
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is False
assert body["data"] is None
assert body["error"]["code"] == "HORAIRES_INVALIDES"

print("\n" + "=" * 60)
print("TEST 6: POST /api/optimiser (validation error - champ manquant)")
code, body = fetch("/api/optimiser", {"activites": [{"nom": "Test"}]})
print(f"Status: {code}")
print(json.dumps(body, indent=2, ensure_ascii=False))
assert body["success"] is False
assert body["data"] is None
assert body["error"]["code"] == "VALIDATION_ERROR"

print("\n" + "=" * 60)
print("✅ TOUS LES TESTS PASSENT")
