import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { viteSingleFile } from "vite-plugin-singlefile";

const isOffline = process.env.BUILD_OFFLINE === "true";

export default defineConfig({
  plugins: [vue(), ...(isOffline ? [viteSingleFile()] : [])],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
    },
  },
});
