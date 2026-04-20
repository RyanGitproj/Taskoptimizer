import { ParametresOptimisation, ResultatOptimisation, ReponseStandard } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
console.log("[DEBUG] API URL:", BASE_URL);

export class ErreurAPI extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ErreurAPI";
  }
}

export async function optimiserPlanning(
  params: ParametresOptimisation,
  source: "manual" | "effect" | "debounce" = "effect"
): Promise<ResultatOptimisation> {
  const payload = JSON.stringify(params);
  if (typeof window !== "undefined") {
    const traceWindow = window as Window & { __lastApiCall?: number };
    const now = Date.now();
    const intervalMs = traceWindow.__lastApiCall ? now - traceWindow.__lastApiCall : null;
    traceWindow.__lastApiCall = now;

    console.log("[API TRIGGER]", {
      heureFin: params.heure_fin_travail,
      activites: params.activites.length,
      source,
      intervalMs,
      at: new Date(now).toISOString(),
    });
  }
  console.log("[API DEBUG] FETCH START");
  console.log("[API DEBUG] Payload keys:", Object.keys(params));
  console.log("[API DEBUG] heure_fin_travail:", params.heure_fin_travail);
  console.log("[API DEBUG] Full JSON:", payload);
  
  const response = await fetch(`${BASE_URL}/api/optimiser`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  });

  const body: ReponseStandard<ResultatOptimisation> = await response.json().catch(
    () => ({ success: false, data: null, error: { code: "NETWORK_ERROR", message: "Erreur de connexion au serveur." } })
  );

  if (!body.success || body.data === null) {
    const err = body.error ?? { code: "UNKNOWN_ERROR", message: `Erreur HTTP ${response.status}` };
    throw new ErreurAPI(err.code, err.message);
  }

  return body.data;
}

export async function verifierSante(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/sante`);
    if (!res.ok) return false;
    const body: ReponseStandard<unknown> = await res.json();
    return body.success;
  } catch {
    return false;
  }
}
