import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const API_PREFIXES = [
  "/auth",
  "/users",
  "/addresses",
  "/categories",
  "/products",
  "/cart",
  "/orders",
  "/admin",
  "/activities",
  "/flash-sale",
  "/fulfillments",
  "/health",
];

const proxy = {};
for (const prefix of API_PREFIXES) {
  proxy[prefix] = "http://127.0.0.1:8000";
}

export default defineConfig({
  plugins: [vue()],
  server: { port: 5173, proxy },
  build: { outDir: "dist", emptyOutDir: true },
});
