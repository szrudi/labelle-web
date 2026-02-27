import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import path from "path";
import { readFileSync } from "fs";
import { config } from "dotenv";

config({ path: path.resolve(__dirname, "../.env") });

const rootPkg = JSON.parse(
  readFileSync(path.resolve(__dirname, "../package.json"), "utf-8"),
);
const backendPort = process.env.PORT || "5000";

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(rootPkg.version),
  },
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Labelle Web",
        short_name: "Labelle",
        start_url: "/",
        display: "standalone",
        theme_color: "#0b6ea8",
        background_color: "#f3f4f6",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: /^.*\/api\/.*/,
            handler: "NetworkFirst",
            options: { cacheName: "api-cache" },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../server/dist-client"),
    emptyOutDir: true,
  },
});
