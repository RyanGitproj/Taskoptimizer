export type Flexibilite = "fixe" | "flexible";

export interface Activite {
  id: string; // uniquement côté front pour la gestion de liste
  nom: string;
  duree: number;
  priorite: number;
  flexibilite: Flexibilite;
  heure_debut_souhaitee?: string;
}

export interface ParametresOptimisation {
  activites: Omit<Activite, "id">[];
  heure_debut_travail: string;
  heure_fin_travail: string;
  duree_pause: number;
}

export interface PlageHoraire {
  activite: string;
  debut: string;
  fin: string;
  priorite: number;
  flexibilite: string;
  est_pause: boolean;
}

export interface ResultatOptimisation {
  planning: PlageHoraire[];
  score_optimisation: number;
  temps_total_planifie: number;
  activites_non_planifiees: string[];
  message: string;
}

export interface ErreurDetail {
  code: string;
  message: string;
}

export interface ReponseStandard<T> {
  success: boolean;
  data: T | null;
  error: ErreurDetail | null;
}
