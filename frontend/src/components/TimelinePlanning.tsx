"use client";

import { PlageHoraire, ResultatOptimisation } from "@/types";
import {
  heureEnMinutes,
  dureeFormatee,
  COULEURS_PRIORITE,
} from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  resultat: ResultatOptimisation;
  heureDebut: string;
  heureFin: string;
}

export default function TimelinePlanning({ resultat, heureDebut, heureFin }: Props) {
  const debutJournee = heureEnMinutes(heureDebut);
  const finJournee = heureEnMinutes(heureFin);
  const dureeJournee = finJournee - debutJournee;

  const positionPourcent = (debut: string): number =>
    ((heureEnMinutes(debut) - debutJournee) / dureeJournee) * 100;

  const largeurPourcent = (debut: string, fin: string): number =>
    ((heureEnMinutes(fin) - heureEnMinutes(debut)) / dureeJournee) * 100;

  // Générer les marqueurs horaires
  const marqueurs: string[] = [];
  for (let m = debutJournee; m <= finJournee; m += 60) {
    const h = Math.floor(m / 60);
    marqueurs.push(`${String(h).padStart(2, "0")}:00`);
  }

  return (
    <div className="space-y-6">
      {/* Métriques */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0 }}
        >
          <MetriqueCard
            label="Score d'optimisation"
            valeur={`${resultat.score_optimisation}%`}
            couleur="indigo"
            icone="◈"
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <MetriqueCard
            label="Temps planifié"
            valeur={dureeFormatee(resultat.temps_total_planifie)}
            couleur="emerald"
            icone="◷"
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <MetriqueCard
            label="Activités planifiées"
            valeur={`${resultat.planning.filter((p) => !p.est_pause).length}`}
            couleur="violet"
            icone="◉"
          />
        </motion.div>
      </div>

      {/* Message */}
      <div className={`text-sm px-4 py-3 rounded-xl font-medium ${
        resultat.activites_non_planifiees.length > 0
          ? "bg-amber-50 text-amber-700 border border-amber-200"
          : "bg-emerald-50 text-emerald-700 border border-emerald-200"
      }`}>
        {resultat.message}
      </div>

      {/* Timeline */}
      <div>
        <h3 className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-4">
          Planning journalier
        </h3>

        {/* Règle horaire */}
        <div className="relative mb-2 h-5">
          {marqueurs.map((h) => (
            <span
              key={h}
              className="absolute text-[10px] text-gray-300 font-mono transform -translate-x-1/2"
              style={{ left: `${positionPourcent(h)}%` }}
            >
              {h}
            </span>
          ))}
        </div>

        {/* Barre timeline */}
        <div className="relative h-14 bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden mb-6">
          {/* Lignes de grille horaire */}
          {marqueurs.map((h) => (
            <div
              key={h}
              className="absolute top-0 bottom-0 w-px bg-gray-100"
              style={{ left: `${positionPourcent(h)}%` }}
            />
          ))}

          {/* Blocs d'activités */}
          <AnimatePresence mode="popLayout">
            {resultat.planning.map((plage, i) => (
              <BlocTimeline
                key={`${plage.activite}-${plage.debut}-${plage.fin}`}
                plage={plage}
                gauche={positionPourcent(plage.debut)}
                largeur={largeurPourcent(plage.debut, plage.fin)}
                index={i}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Légende détaillée */}
        <div className="space-y-2">
          <AnimatePresence>
            {resultat.planning.map((plage, i) => (
              <motion.div
                key={`${plage.activite}-${plage.debut}-${plage.fin}-ligne`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, delay: 0.3 + i * 0.05 }}
              >
                <LignePlanning plage={plage} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Activités non planifiées */}
      {resultat.activites_non_planifiees.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-3">
            Non planifiées (contraintes impossibles)
          </h3>
          <div className="flex flex-wrap gap-2">
            {resultat.activites_non_planifiees.map((nom, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-red-50 text-red-500 border border-red-100 rounded-full text-xs font-medium"
              >
                {nom}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sous-composants
// ---------------------------------------------------------------------------

function MetriqueCard({
  label,
  valeur,
  couleur,
  icone,
}: {
  label: string;
  valeur: string;
  couleur: "indigo" | "emerald" | "violet";
  icone: string;
}) {
  const classes = {
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-100",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-100",
    violet: "bg-violet-50 text-violet-700 border-violet-100",
  };
  return (
    <div className={`border rounded-2xl p-4 ${classes[couleur]}`}>
      <div className="text-lg mb-1">{icone}</div>
      <div className="text-xl font-bold">{valeur}</div>
      <div className="text-xs opacity-70 mt-1">{label}</div>
    </div>
  );
}

function BlocTimeline({
  plage,
  gauche,
  largeur,
  index,
}: {
  plage: PlageHoraire;
  gauche: number;
  largeur: number;
  index: number;
}) {
  if (plage.est_pause) {
    return (
      <motion.div
        initial={{ opacity: 0, scaleX: 0 }}
        animate={{ opacity: 1, scaleX: 1 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className="absolute top-1 bottom-1 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center"
        style={{ left: `${gauche}%`, width: `${Math.max(largeur, 0.5)}%` }}
        title="Pause"
      >
        {largeur > 3 && (
          <span className="text-[10px] text-blue-400 font-semibold flex items-center gap-1">
            ⏸ Pause
          </span>
        )}
      </motion.div>
    );
  }

  const couleur = COULEURS_PRIORITE[plage.priorite];

  return (
    <motion.div
      initial={{ opacity: 0, scaleX: 0 }}
      animate={{ opacity: 1, scaleX: 1 }}
      exit={{ opacity: 0, scaleX: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="absolute top-1 bottom-1 rounded-lg flex items-center px-1.5 overflow-hidden cursor-default"
      style={{
        left: `${gauche}%`,
        width: `${Math.max(largeur, 1)}%`,
        backgroundColor: couleur + "22",
        borderLeft: `3px solid ${couleur}`,
      }}
      title={`${plage.activite} — ${plage.debut} à ${plage.fin}`}
    >
      {largeur > 6 && (
        <span className="text-[9px] font-semibold truncate" style={{ color: couleur }}>
          {plage.activite}
        </span>
      )}
    </motion.div>
  );
}

function LignePlanning({ plage }: { plage: PlageHoraire }) {
  if (plage.est_pause) {
    const duree = heureEnMinutes(plage.fin) - heureEnMinutes(plage.debut);
    return (
      <div className="flex items-center gap-3 py-2.5 px-4 bg-blue-50 border border-blue-100 rounded-xl">
        <div className="text-lg flex-shrink-0">⏸</div>
        <span className="text-xs text-blue-400 font-mono w-24 flex-shrink-0">
          {plage.debut} → {plage.fin}
        </span>
        <span className="text-sm font-semibold text-blue-600 flex-1">Pause</span>
        <span className="text-xs text-blue-400 flex-shrink-0">{dureeFormatee(duree)}</span>
      </div>
    );
  }

  const couleur = COULEURS_PRIORITE[plage.priorite];
  const duree = heureEnMinutes(plage.fin) - heureEnMinutes(plage.debut);

  return (
    <div className="flex items-center gap-3 py-2.5 px-4 bg-white border border-gray-100 rounded-xl hover:border-gray-200 transition-colors">
      <div
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: couleur }}
      />
      <span className="text-xs text-gray-400 font-mono w-24 flex-shrink-0">
        {plage.debut} → {plage.fin}
      </span>
      <span className="text-sm font-medium text-gray-700 flex-1 truncate">{plage.activite}</span>
      <span className="text-xs text-gray-400 flex-shrink-0">{dureeFormatee(duree)}</span>
      <span
        className="text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0"
        style={{ color: couleur, backgroundColor: couleur + "18" }}
      >
        P{plage.priorite}
      </span>
    </div>
  );
}
