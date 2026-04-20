# 🧠 TaskOptimizer

Optimisez intelligemment votre planning quotidien grâce à la programmation par contraintes.

---

## 🚀 Présentation

TaskOptimizer est une application web qui génère automatiquement un planning optimal à partir d'une liste d'activités.

**Objectif :** Maximiser la productivité tout en respectant :
- les contraintes de temps
- les priorités
- les tâches fixes

---

## ✨ Fonctionnalités

- Génération automatique de planning
- Recalcul dynamique (auto-update)
- Gestion des priorités (1 à 5)
- Support des tâches fixes avec heure souhaitée
- Gestion des tâches flexibles
- 3 modes de placement :
  - **Compact** : Tâches regroupées au plus tôt
  - **Uniforme** : Temps libre réparti régulièrement
  - **Intelligent** : Priorités hautes plus tôt, blanc final limité
- Détection des conflits entre tâches fixes
- Système de fair sharing (récompense par paliers, anti-waste)
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
- Tâches fixes respectées (heure souhaitée obligatoire)
- Détection des conflits entre tâches fixes

**Objectif (Fair Sharing) :**
- Maximiser la somme pondérée des tâches selon leur priorité
- Récompense par paliers pour les gaps :
  - 0-20 min : 5000 points (vital)
  - 20-60 min : 2000 points (confortable)
- Pénalité anti-waste : gaps > 90 min (-15000 points)
- Réduction de la pression de fin pour permettre l'étalement
- Mode intelligent : attraction vers le matin pour les priorités P5/P4

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

# Copier l'exemple de configuration
cp .env.example .env

# Modifier .env si nécessaire (par défaut : localhost:3000)
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Copier l'exemple de configuration
cp .env.local.example .env.local

# Modifier .env.local si nécessaire (par défaut : localhost:8000)
npm run dev
```

---

## 🔧 Configuration (Variables d'environnement)

### Backend (.env)

- `ALLOWED_ORIGINS` : Liste des origines autorisées pour CORS (séparées par virgule)
  - Développement : `http://localhost:3000,http://127.0.0.1:3000`
  - Production : `https://your-frontend-domain.com,https://another-domain.com`

### Frontend (.env.local)

- `NEXT_PUBLIC_API_URL` : URL de l'API backend
  - Développement : `http://localhost:8000`
  - Production : `https://your-backend-domain.com`

---

## 🧪 Utilisation

1. Ajouter des activités avec :
   - Nom, durée, priorité (1-5)
   - Flexibilité (fixe ou flexible)
   - Heure souhaitée (pour les tâches fixes)
2. Définir horaires de travail
3. Choisir le mode de placement :
   - **Compact** : Tâches regroupées au début
   - **Uniforme** : Temps libre réparti régulièrement
   - **Intelligent** : Priorités hautes plus tôt (recommandé)
4. Lancer l'optimisation
5. Visualiser le planning généré
6. Exporter en PDF

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
