"use client";

interface Props {
  heureDebut: string;
  heureFin: string;
  dureePause: number;
  onChangeDebut: (v: string) => void;
  onChangeFin: (v: string) => void;
  onChangePause: (v: number) => void;
}

export default function ParametresPanel({
  heureDebut,
  heureFin,
  dureePause,
  onChangeDebut,
  onChangeFin,
  onChangePause,
}: Props) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
      <h2 className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-4">
        Paramètres de la journée
      </h2>
      <div className="grid grid-cols-3 gap-4">
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
          <label className="block text-xs text-gray-500 mb-1">
            Pause (min) — {dureePause} min
          </label>
          <input
            type="range"
            min={0}
            max={30}
            step={5}
            value={dureePause}
            onChange={(e) => onChangePause(parseInt(e.target.value))}
            className="w-full mt-2 accent-indigo-600"
          />
        </div>
      </div>
    </div>
  );
}
