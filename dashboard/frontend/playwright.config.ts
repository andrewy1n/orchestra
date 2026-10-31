import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.E2E_PORT ?? 4173);
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
	testDir: "./e2e",
	fullyParallel: false,
	workers: 1,
	forbidOnly: !!process.env.CI,
	reporter: process.env.CI ? "github" : "list",
	use: {
		baseURL: BASE_URL,
		headless: true,
		trace: "retain-on-failure",
	},
	projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
	webServer: {
		command: `uv run python e2e/serve.py --port ${PORT}`,
		url: BASE_URL,
		reuseExistingServer: false,
		gracefulShutdown: { signal: "SIGTERM", timeout: 10_000 },
		timeout: 120_000,
	},
});
