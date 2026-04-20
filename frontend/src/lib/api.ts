import { ParametresOptimisation, ResultatOptimisation, ReponseStandard } from "@/types";

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL as string) ?? "http://localhost:8000";

export class ErreurAPI extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ErreurAPI";
  }
}

export async function optimiserPlanning(
  params: ParametresOptimisation
): Promise<ResultatOptimisation> {
  const payload = JSON.stringify(params);
  
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
    console.error("Erreur API:", err);
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
