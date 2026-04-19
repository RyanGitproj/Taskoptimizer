import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Le frontend communique avec le backend FastAPI via variable d'environnement
  // NEXT_PUBLIC_API_URL (défaut : http://localhost:8000)
};

export default nextConfig;
