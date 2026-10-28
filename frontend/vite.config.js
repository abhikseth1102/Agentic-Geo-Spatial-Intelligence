import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "react-vendor",
              test: /node_modules[\\/]react(?:-dom)?[\\/]/,
              priority: 30,
            },
            {
              name: "maps",
              test: /node_modules[\\/](?:leaflet|react-leaflet|@react-leaflet)[\\/]/,
              priority: 20,
            },
            {
              name: "charts",
              test: /node_modules[\\/](?:recharts|d3-[^\\/]+|victory-vendor)[\\/]/,
              priority: 15,
            },
            { name: "coastline", test: /coastline\.json/, priority: 10 },
          ],
        },
      },
    },
  },
  server: { host: "127.0.0.1", proxy: { "/api": "http://127.0.0.1:8080" } },
});
