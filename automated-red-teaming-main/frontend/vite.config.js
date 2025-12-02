import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  // base: "/art/", // adds /art prefix to assets for build because of GCLB routing path.
  plugins: [react(), tailwindcss()],
});
