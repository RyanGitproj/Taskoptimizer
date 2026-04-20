"use client";

import { Activite, Flexibilite } from "@/types";
import { COULEURS_PRIORITE, LABELS_PRIORITE } from "@/lib/utils";
import { motion } from "framer-motion";

interface Props {
  activite: Activite;
  index: number;
  onModifier: (id: string, champ: keyof Activite, valeur: string | number) => void;
  onSupprimer: (id: string) => void;
}

export default function ActiviteCard({ activite, index, onModifier, onSupprimer }: Props) {
  const couleur = COULEURS_PRIORITE[activite.priorite];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className="relative bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow duration-200"
      style={{ borderLeft: `4px solid ${couleur}` }}
    >
      {/* En-tête */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">
          Activité {index + 1}
        </span>
        <button
          onClick={() => onSupprimer(activite.id)}
          className="text-gray-300 hover:text-red-400 transition-colors duration-150 text-lg leading-none"
          aria-label="Supprimer"
        >
          ×
        </button>
      </div>

      {/* Nom */}
      <div className="mb-3">
        <input
          type="text"
          value={activite.nom}
          onChange={(e) => onModifier(activite.id, "nom", e.target.value)}
          placeholder="Nom de l'activité"
          className="w-full text-sm font-medium text-gray-800 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 placeholder-gray-300 transition"
        />
      </div>

      {/* Durée + Priorité */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Durée (min)</label>
          <input
            type="number"
            value={activite.duree === 0 ? "" : activite.duree}
            placeholder="0"
            min={1}
            max={480}
            onChange={(e) => {
              const val = e.target.value === "" ? 0 : parseInt(e.target.value);
              onModifier(activite.id, "duree", isNaN(val) ? 0 : val);
            }}
            className="w-full text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Priorité —{" "}
            <span style={{ color: couleur }} className="font-semibold">
              {LABELS_PRIORITE[activite.priorite]}
            </span>
          </label>
          <input
            type="range"
            min={1}
            max={5}
            value={activite.priorite}
            onChange={(e) => onModifier(activite.id, "priorite", parseInt(e.target.value))}
            className="w-full accent-indigo-600 mt-1"
          />
        </div>
      </div>

      {/* Flexibilité */}
      <div className="mb-3">
        <label className="block text-xs text-gray-400 mb-2">Flexibilité</label>
        <div className="flex gap-2">
          {(["flexible", "fixe"] as Flexibilite[]).map((f) => (
            <button
              key={f}
              onClick={() => onModifier(activite.id, "flexibilite", f)}
              className={`flex-1 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-150 ${
                activite.flexibilite === f
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-gray-500 border-gray-200 hover:border-indigo-300"
              }`}
            >
              {f === "flexible" ? "⟳ Flexible" : "⚓ Fixe"}
            </button>
          ))}
        </div>
      </div>

      {/* Heure souhaitée si fixe */}
      {activite.flexibilite === "fixe" && (
        <div>
          <label className="block text-xs text-gray-400 mb-1">Heure souhaitée</label>
          <input
            type="time"
            value={activite.heure_debut_souhaitee ?? "09:00"}
            onChange={(e) => onModifier(activite.id, "heure_debut_souhaitee", e.target.value)}
            className="w-full text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition"
          />
        </div>
      )}
    </motion.div>
  );
}
