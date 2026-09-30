import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 11225,
    host: "127.0.0.1",
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:11226",
      "/skill": "http://127.0.0.1:11226",
    },
  },
  preview: { port: 11225, host: "127.0.0.1" },
});
