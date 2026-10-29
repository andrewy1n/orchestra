/// <reference types="vitest/config" />

import { fileURLToPath } from "node:url";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";
import { API_TARGET } from "./src/api.ts";

// The FastAPI server the dev server proxies to. Override for a custom port.
const target = process.env.DASHBOARD_API_TARGET ?? API_TARGET;

// https://vite.dev/config/
export default defineConfig({
	plugins: [svelte(), tailwindcss()],
	server: {
		host: "127.0.0.1",
		// The Svelte app talks to a same-origin `/api`; the dev server forwards it
		// to the FastAPI server so no CORS headers are involved.
		proxy: {
			"/api": { target, changeOrigin: false },
		},
	},
	test: {
		environment: "jsdom",
		include: ["src/**/*.test.ts"],
	},
	// Vitest runs in Node but the components are client code; resolve the
	// browser build of Svelte so `mount` works.
	resolve: {
		alias: { $lib: fileURLToPath(new URL("./src/lib", import.meta.url)) },
		conditions: process.env.VITEST ? ["browser"] : undefined,
	},
});
