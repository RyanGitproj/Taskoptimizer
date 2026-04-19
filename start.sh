#!/usr/bin/env bash
# ============================================================
# TaskOptimizer — Script de démarrage rapide
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      TaskOptimizer — Démarrage           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Backend ──────────────────────────────────────
echo "▶ Installation des dépendances backend..."
cd backend
pip install -r requirements.txt --quiet
echo "▶ Démarrage du serveur FastAPI (port 8000)..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# ── Frontend ─────────────────────────────────────
echo "▶ Installation des dépendances frontend..."
cd frontend
npm install --silent
echo "▶ Démarrage du serveur Next.js (port 3000)..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Serveurs démarrés :"
echo "   Backend  → http://localhost:8000"
echo "   Frontend → http://localhost:3000"
echo "   API Docs → http://localhost:8000/docs"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
