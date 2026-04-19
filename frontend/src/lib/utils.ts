export function heureEnMinutes(heure: string): number {
  const [h, m] = heure.split(":").map(Number);
  return h * 60 + m;
}

export function minutesEnHeure(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function dureeFormatee(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

export const COULEURS_PRIORITE: Record<number, string> = {
  1: "#6B7280",
  2: "#3B82F6",
  3: "#8B5CF6",
  4: "#F59E0B",
  5: "#EF4444",
};

export const LABELS_PRIORITE: Record<number, string> = {
  1: "Très basse",
  2: "Basse",
  3: "Moyenne",
  4: "Haute",
  5: "Critique",
};

export function genererIdUnique(): string {
  return Math.random().toString(36).slice(2, 9);
}
