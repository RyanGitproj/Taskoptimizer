"use client";

import { ModePlacement } from "@/types";

interface Props {
  heureDebut: string;
  heureFin: string;
  modePlacement: ModePlacement;
  onChangeDebut: (v: string) => void;
  onChangeFin: (v: string) => void;
  onChangeModePlacement: (v: ModePlacement) => void;
}

export default function ParametresPanel({
  heureDebut,
  heureFin,
  modePlacement,
  onChangeDebut,
  onChangeFin,
  onChangeModePlacement,
}: Props) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
      <h2 className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-4">
        Paramètres de la journée
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Début de journée</label>
          <input
            type="time"
            value={heureDebut}
            onChange={(e) => onChangeDebut(e.target.value)}
            className="w-full text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Fin de journée</label>
          <input
            type="time"
            value={heureFin}
            onChange={(e) => onChangeFin(e.target.value)}
            className="w-full text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Mode de placement</label>
          <select
            value={modePlacement}
            onChange={(e) => onChangeModePlacement(e.target.value as ModePlacement)}
            className="w-full text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition"
          >
            <option value="intelligent">Intelligent (recommandé)</option>
            <option value="uniforme">Uniforme</option>
            <option value="compact">Compact</option>
          </select>
          <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
            Intelligent: priorités hautes plus tôt, blanc final limité. Uniforme: temps libre réparti
            régulièrement. Compact: tâches regroupées au plus tôt.
          </p>
        </div>
      </div>
    </div>
  );
}
