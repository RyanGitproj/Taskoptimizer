# 🧠 TaskOptimizer

Optimisez intelligemment votre planning quotidien grâce à la programmation par contraintes.

---

## 🚀 Présentation

TaskOptimizer est une application web qui génère automatiquement un planning optimal à partir d'une liste d'activités.

**Objectif :** Maximiser la productivité tout en respectant :
- les contraintes de temps
- les priorités
- les tâches fixes
- les pauses

---

## ✨ Fonctionnalités

- Génération automatique de planning
- Recalcul dynamique (auto-update)
- Gestion des priorités (1 à 5)
- Support des tâches fixes
- Gestion des tâches flexibles
- Découpage automatique des tâches longues (>90 min en 2 segments)
- Insertion intelligente de pauses
- Score d'optimisation
- Export PDF
- Interface fluide avec animations

---

## 🏗️ Architecture

```
Frontend → API → Service → Solver → Post-processing → Output
```

### Frontend
- React (Next.js)
- TypeScript
- Tailwind CSS
- Framer Motion

### Backend
- FastAPI
- Pydantic
- OR-Tools (CP-SAT)

---

## 🧠 Logique d'optimisation

### Optimisation (OR-Tools)

**Variables :** début, fin, planifiée

**Contraintes :**
- Pas de chevauchement
- Respect des horaires
- Tâches fixes respectées

**Objectif :** Maximiser la somme pondérée des tâches selon leur priorité

### Gestion des pauses

**IMPORTANT :** Les pauses ne sont pas dans OR-Tools. Elles sont ajoutées après optimisation (post-processing).

**Règles :**
- Pause après tâche ≥ 60 min
- Maximum 2 tâches consécutives sans pause

---

## ⚙️ Installation

### Backend

```bash
cd backend
python -m venv venv
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Utilisation

1. Ajouter des activités
2. Définir horaires et paramètres
3. Lancer l'optimisation
4. Visualiser le planning
5. Exporter en PDF

---

## 🎯 Objectif du projet

Ce projet démontre :
- l'utilisation de la programmation par contraintes
- la modélisation de problèmes réels
- une architecture fullstack propre
- une séparation claire logique métier / optimisation
---

## 🔧 Stack technique

- **Frontend :** Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion
- **Backend :** FastAPI, Pydantic, Google OR-Tools CP-SAT
- **Export :** jsPDF
