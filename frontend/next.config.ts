import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /api/chat → FastAPI backend (avoids CORS in dev)
  async rewrites() {
    return [];  // We proxy inside the API route instead
  },
  // Allow images from any HTTPS source (for future nutrition food images)
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
};

export default nextConfig;
