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
      allowedHosts: ["fitnesstracker.local"],
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
      // When behind Nginx (https://fitnesstracker.local), the HMR WebSocket
      // must connect back on port 443, not the internal Vite port 5173.
      // Set VITE_HMR_CLIENT_PORT=443 in .env for the Docker/Nginx setup.
      hmr: env.VITE_HMR_CLIENT_PORT
        ? { clientPort: parseInt(env.VITE_HMR_CLIENT_PORT) }
        : true,
    },
  };
});
