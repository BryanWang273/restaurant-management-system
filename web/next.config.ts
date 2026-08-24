import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pins the workspace root to this project so Turbopack doesn't try to walk
  // up to a package-lock.json it finds in the user's home directory.
  turbopack: {
    root: path.join(__dirname),
  },
  // The dev server was started bound to "localhost", so it only trusts
  // requests whose Host header says "localhost" by default. The preview
  // browser here loads it via "127.0.0.1", which Next.js's dev-origin CSRF
  // guard otherwise blocks (assets 403, HMR socket refused, no hydration).
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
