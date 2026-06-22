import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  // Inside docker-compose this points at the `backend` service; on a bare
  // host machine it falls back to localhost.
  const proxyTarget = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      host: true, // bind 0.0.0.0 so docker exposes us on the host
      allowedHosts: ["fittrack.local"],
      port: 5173,
      strictPort: true,
      watch: {
        // Polling is needed for hot-reload over bind mounts on Windows/macOS.
        usePolling: true,
        interval: 300,
      },
      proxy: {
        "/api": { target: proxyTarget, changeOrigin: true },
        "/media": { target: proxyTarget, changeOrigin: true },
      },
      // No clientPort override: with hmr=true Vite's client connects back on
      // whatever host:port the page was loaded from. That makes HMR work both
      // directly (http://localhost:5173) and behind Nginx
      // (https://fittrack.local → wss on 443), with no env switching.
      hmr: true,
    },
  };
});
