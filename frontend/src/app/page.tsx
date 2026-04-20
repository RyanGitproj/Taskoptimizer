"use client";

import { useState, useEffect, useRef } from "react";
import { Activite, ResultatOptimisation } from "@/types";
import { optimiserPlanning, ErreurAPI } from "@/lib/api";
import { genererIdUnique } from "@/lib/utils";
import { exporterPlanningPDF } from "@/lib/pdf";
import { AnimatePresence, motion } from "framer-motion";
import ActiviteCard from "@/components/ActiviteCard";
import ParametresPanel from "@/components/ParametresPanel";
import TimelinePlanning from "@/components/TimelinePlanning";

const ACTIVITE_VIDE = (): Activite => ({
  id: genererIdUnique(),
  nom: "",
  duree: 60,
  priorite: 3,
  flexibilite: "flexible",
});

const ACTIVITES_EXEMPLES: Activite[] = [
  { id: genererIdUnique(), nom: "Revue de code", duree: 90, priorite: 5, flexibilite: "fixe", heure_debut_souhaitee: "09:00" },
  { id: genererIdUnique(), nom: "Réunion d'équipe", duree: 60, priorite: 4, flexibilite: "fixe", heure_debut_souhaitee: "11:00" },
  { id: genererIdUnique(), nom: "Développement feature", duree: 120, priorite: 5, flexibilite: "flexible" },
  { id: genererIdUnique(), nom: "Documentation", duree: 45, priorite: 2, flexibilite: "flexible" },
  { id: genererIdUnique(), nom: "Veille technologique", duree: 30, priorite: 3, flexibilite: "flexible" },
];

export default function PagePrincipale() {
  const [activites, setActivites] = useState<Activite[]>(ACTIVITES_EXEMPLES);
  const [heureDebut, setHeureDebut] = useState("09:00");
  const [heureFin, setHeureFin] = useState("18:00");
  const [dureePause, setDureePause] = useState(15);
  const [resultat, setResultat] = useState<ResultatOptimisation | null>(null);
  const [chargement, setChargement] = useState(false);
  const [chargementAuto, setChargementAuto] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [succesVisible, setSuccesVisible] = useState(false);
  const [view, setView] = useState<"input" | "result">("input"); // Explicit view state
  const [optimisationToken, setOptimisationToken] = useState(0);
  const isNavigatingRef = useRef(false);
  const isOptimizingRef = useRef(false);
  const isAutoCallRef = useRef(false); // Prevent feedback loop on auto calls

  // Global API call tracking
  if (typeof window !== "undefined") {
    (window as any).__lastApiCall = (window as any).__lastApiCall || null;
  }

  // Un seul trigger API: cet effect s'exécute uniquement quand l'utilisateur clique "Lancer l'optimisation".
  useEffect(() => {
    console.log("[USE EFFECT TRIGGERED]", { optimisationToken });
    if (optimisationToken === 0) return;
    if (isOptimizingRef.current) {
      console.log("[API GUARD] Skipping - API call already in progress");
      return;
    }

    const executerOptimisation = async () => {
      console.log("[EXECUTING OPTIMISATION]", { optimisationToken });
      isOptimizingRef.current = true;
      
      const valides = activites.filter((a) => a.nom.trim().length > 0);
      if (valides.length === 0) {
        setErreur("Veuillez ajouter au moins une activité avec un nom.");
        setChargement(false);
        isOptimizingRef.current = false;
        return;
      }

      const requestId = Math.floor(Math.random() * 10000);
      const payloadSnapshot = {
        activites: valides.map(({ id: _id, ...rest }) => rest), // eslint-disable-line @typescript-eslint/no-unused-vars
        heure_debut_travail: heureDebut,
        heure_fin_travail: heureFin,
        duree_pause: dureePause,
      };

      // Track API call interval
      const now = Date.now();
      const lastCall = (window as any).__lastApiCall;
      const interval = lastCall ? now - lastCall : null;
      (window as any).__lastApiCall = now;

      console.log(`[REQ-${requestId}] EXÉCUTION - Source: clic utilisateur`);
      console.log(`[REQ-${requestId}] FINAL PAYLOAD:`, payloadSnapshot);
      console.log("[API TRIGGER]", {
        heureFin,
        activites: payloadSnapshot.activites.length,
        source: "effect",
        intervalSinceLastCall: interval,
        lastCallTimestamp: lastCall,
      });

      try {
        const res = await optimiserPlanning(payloadSnapshot);
        console.log(`[REQ-${requestId}] RÉUSSI`);
        setResultat(res);
        setErreur(null);
        setView("result");
        setSuccesVisible(true);
        setTimeout(() => setSuccesVisible(false), 3000);
      } catch (e: unknown) {
        console.error(`[REQ-${requestId}] ERREUR:`, e);
        if (e instanceof ErreurAPI) {
          setErreur(e.message);
        } else {
          setErreur("Erreur de connexion au serveur.");
        }
      } finally {
        setChargement(false);
        isOptimizingRef.current = false;
      }
    };

    executerOptimisation();
  }, [optimisationToken]); // Only trigger when user clicks button

  const ajouterActivite = () => {
    if (activites.length >= 20) return;
    setActivites((prev) => [...prev, ACTIVITE_VIDE()]);
  };

  const supprimerActivite = (id: string) => {
    setActivites((prev) => prev.filter((a) => a.id !== id));
  };

  const modifierActivite = (id: string, champ: keyof Activite, valeur: string | number) => {
    setActivites((prev) =>
      prev.map((a) => (a.id === id ? { ...a, [champ]: valeur } : a))
    );
  };

  const lancerOptimisation = () => {
    console.log("[LANCER_OPTIMISATION CALLED]", {
      heureFin,
      activites: activites.filter((a) => a.nom.trim().length > 0).length,
      source: "manual",
      currentToken: optimisationToken,
    });
    setErreur(null);
    setResultat(null);
    setChargement(true);
    setOptimisationToken((prev) => {
      console.log("[TOKEN INCREMENT]", { from: prev, to: prev + 1 });
      return prev + 1;
    });
  };

  const reinitialiser = () => {
    console.log("[DEBUG] reinitialiser called - setting view to input");
    setView("input");
    setResultat(null);
    setErreur(null);
  };

  const handleHeureDebutChange = (valeur: string) => {
    setHeureDebut(valeur);
  };

  const handleHeureFinChange = (valeur: string) => {
    if (!valeur) return; // Sécurité contre les valeurs vides
    console.log("[DEBUG] User changed heureFin to:", valeur);
    setHeureFin(valeur);
  };

  const handleDureePauseChange = (valeur: number) => {
    setDureePause(valeur);
  };

  return (
    <div className="min-h-screen bg-[#F8F8FB] font-sans">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white px-8 py-5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-white text-sm font-bold">T</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900 tracking-tight">TaskOptimizer</h1>
              <p className="text-[10px] text-gray-400 tracking-widest uppercase">
                Moteur de planification par contraintes
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
            OR-Tools CP-SAT
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-8">
        <AnimatePresence mode="wait">
          {view === "input" ? (
            <motion.div
              key="input"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">
                Définir vos activités
              </h2>
              <p className="text-sm text-gray-400">
                Le moteur d&#39;optimisation générera automatiquement votre planning optimal.
              </p>
            </div>

            {/* Paramètres globaux */}
            <ParametresPanel
              heureDebut={heureDebut}
              heureFin={heureFin}
              dureePause={dureePause}
              onChangeDebut={handleHeureDebutChange}
              onChangeFin={handleHeureFinChange}
              onChangePause={handleDureePauseChange}
            />

            {/* Grille d'activités */}
            {activites.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="border-2 border-dashed border-gray-200 rounded-2xl p-12 flex flex-col items-center justify-center gap-4 text-center"
              >
                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                  <span className="text-3xl">📋</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-1">Aucune activité</h3>
                  <p className="text-sm text-gray-400 mb-4">
                    Commencez par ajouter votre première activité pour générer un planning optimal.
                  </p>
                  <button
                    onClick={ajouterActivite}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200"
                  >
                    + Ajouter une activité
                  </button>
                </div>
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <AnimatePresence mode="popLayout">
                  {activites.map((activite, index) => (
                    <ActiviteCard
                      key={activite.id}
                      activite={activite}
                      index={index}
                      onModifier={modifierActivite}
                      onSupprimer={supprimerActivite}
                    />
                  ))}
                </AnimatePresence>

                {/* Bouton ajout */}
                {activites.length < 20 && (
                  <button
                    onClick={ajouterActivite}
                    className="border-2 border-dashed border-gray-200 rounded-2xl p-5 flex flex-col items-center justify-center gap-2 text-gray-300 hover:border-indigo-300 hover:text-indigo-400 transition-all duration-200 min-h-[180px]"
                  >
                    <span className="text-3xl leading-none">+</span>
                    <span className="text-xs font-medium">Ajouter une activité</span>
                  </button>
                )}
              </div>
            )}

            {/* Erreur */}
            {erreur && (
              <div className="bg-red-50 border border-red-100 text-red-600 text-sm px-4 py-3 rounded-xl">
                {erreur}
              </div>
            )}

            {/* Bouton optimisation */}
            <div className="flex justify-center pt-2">
              <button
                onClick={lancerOptimisation}
                disabled={chargement}
                className="relative bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold px-10 py-4 rounded-2xl text-sm tracking-wide transition-all duration-200 shadow-lg shadow-indigo-200 hover:shadow-indigo-300 disabled:shadow-none flex items-center gap-3"
              >
                {chargement ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Optimisation en cours…
                  </>
                ) : (
                  <>
                    <span className="text-base">◈</span>
                    Lancer l&#39;optimisation
                  </>
                )}
              </button>
            </div>
          </motion.div>
        ) : (
          /* ——— VUE RÉSULTAT ——— */
          <motion.div
            key="result"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20, pointerEvents: "none" }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-1">Planning optimisé</h2>
                <p className="text-sm text-gray-400">
                  Généré par OR-Tools CP-SAT — {activites.filter((a) => a.nom.trim()).length} activités analysées
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => resultat && exporterPlanningPDF(resultat, heureDebut, heureFin)}
                  className="text-sm text-gray-600 hover:text-indigo-600 border border-gray-200 hover:border-indigo-300 px-4 py-2 rounded-xl transition-all duration-150"
                >
                  📄 Exporter PDF
                </button>
                <button
                  onClick={reinitialiser}
                  className="text-sm text-gray-400 hover:text-gray-700 border border-gray-200 hover:border-gray-300 px-4 py-2 rounded-xl transition-all duration-150"
                >
                  ← Modifier
                </button>
              </div>
            </div>

            {/* Message résumé utilisateur */}
            {resultat && (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm px-4 py-3 rounded-xl">
                {resultat.activites_non_planifiees.length === 0
                  ? `Planning optimisé avec succès — Score : ${resultat.score_optimisation}%`
                  : `Optimisation partielle — Score : ${resultat.score_optimisation}% — ${resultat.activites_non_planifiees.length} activité(s) non planifiée(s)`}
              </div>
            )}

            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              {resultat && (
                <TimelinePlanning
                  resultat={resultat}
                  heureDebut={heureDebut}
                  heureFin={heureFin}
                />
              )}
            </div>
          </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="text-center py-8 text-xs text-gray-300">
        TaskOptimizer — Moteur CP-SAT · Google OR-Tools · FastAPI · Next.js
      </footer>

      {/* Toast de succès */}
      <AnimatePresence>
        {succesVisible && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-emerald-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3 z-50"
          >
            <span className="text-xl">✓</span>
            <span className="text-sm font-medium">Planning optimisé avec succès !</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
