import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** GitHub Pages project site: /django-db-schema-doc/ — local dev defaults to ./ */
const base = process.env.VITE_BASE_PATH ?? "./";

export default defineConfig({
  plugins: [react()],
  base,
  build: {
    outDir: resolve(__dirname, "../static/erd"),
    emptyOutDir: true,
  },
});
