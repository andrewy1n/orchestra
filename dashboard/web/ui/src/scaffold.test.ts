// @vitest-environment jsdom
/**
 * Scaffold acceptance cases for the web dashboard UI.
 *
 * R31: the Vite dev server proxies /api to the FastAPI server.
 * R35: a fresh load of the page uses the light theme.
 * R36: a theme control switches the document between dark and light.
 *
 * There is no frozen UI oracle yet, so these are the authored cases for the
 * scaffold. They exercise the real `vite.config.ts` (via Vite's own config
 * loader), the real theme module, and the real component's source. When the
 * Svelte plugin is available the component is mounted for real and its theme
 * control is clicked; when the acceptance harness runs vitest from the repo
 * root the plugin is not loaded, so the control is exercised through the same
 * functions the component calls.
 */

import { readFileSync } from "node:fs";
import { createServer as createHttpServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { createServer as createNetServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import {
	createServer as createViteServer,
	loadConfigFromFile,
	type ViteDevServer,
} from "vite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { API_TARGET } from "./api";
import { applyTheme, DEFAULT_THEME, type Theme, toggle } from "./theme";

const here = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.resolve(here, "..");
const configFile = path.join(uiRoot, "vite.config.ts");
const appSource = readFileSync(path.join(here, "App.svelte"), "utf8");

let mounted: ReturnType<typeof mount> | undefined;

function resetDocument() {
	if (mounted) {
		unmount(mounted);
		mounted = undefined;
	}
	const root = document.documentElement;
	root.classList.remove("dark");
	delete root.dataset.theme;
	root.style.colorScheme = "";
	document.body.innerHTML = "";
}

beforeEach(() => {
	resetDocument();
	window.location.hash = "";
});

afterEach(() => {
	resetDocument();
	vi.unstubAllGlobals();
});

/**
 * Mount the real `<App>` when the Svelte plugin is present (vitest run from
 * `dashboard/web/ui`). Returns false when the harness ran vitest from the repo
 * root, where the ui Vite config is not loaded.
 */
async function tryMountApp(): Promise<boolean> {
	try {
		const module = await import("./App.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		flushSync();
		return true;
	} catch {
		mounted = undefined;
		return false;
	}
}

/** A free loopback port. */
async function freePort(): Promise<number> {
	return await new Promise<number>((resolve, reject) => {
		const probe = createNetServer();
		probe.once("error", reject);
		probe.listen(0, "127.0.0.1", () => {
			const { port } = probe.address() as AddressInfo;
			probe.close(() => resolve(port));
		});
	});
}

/** A stub upstream that echoes the request path as JSON. */
async function startUpstream(): Promise<{ server: Server; target: string }> {
	const server = createHttpServer((req, res) => {
		res.setHeader("content-type", "application/json");
		res.end(JSON.stringify({ path: req.url }));
	});
	await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
	const { port } = server.address() as AddressInfo;
	return { server, target: `http://127.0.0.1:${port}` };
}

function closeServer(server: Server): Promise<void> {
	return new Promise<void>((resolve) => server.close(() => resolve()));
}

describe("web-dashboard scaffold", () => {
	it("R31: the Vite dev server proxies /api to the FastAPI server", async () => {
		const loaded = await loadConfigFromFile(
			{ command: "serve", mode: "development" },
			configFile,
		);
		expect(loaded, "vite.config.ts must load").toBeTruthy();

		const proxy = loaded!.config.server?.proxy as
			| Record<string, { target?: string }>
			| undefined;
		expect(proxy, "vite.config.ts must define server.proxy").toBeTruthy();

		const api = proxy!["/api"];
		expect(api, "server.proxy must forward the '/api' prefix").toBeTruthy();
		expect(String(api.target)).toBe(API_TARGET);
		// The FastAPI server binds loopback only.
		expect(API_TARGET).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/);

		// Round trip: a request the config would proxy reaches the FastAPI target.
		const { server: upstream, target } = await startUpstream();
		const port = await freePort();
		let vite: ViteDevServer | undefined;
		try {
			vite = await createViteServer({
				configFile: false,
				root: uiRoot,
				logLevel: "silent",
				server: {
					host: "127.0.0.1",
					port,
					strictPort: true,
					// The proxy the config declares, pointed at the stub upstream.
					proxy: { "/api": { ...api, target } },
				},
			});
			await vite.listen();
			const bound = (vite.httpServer!.address() as AddressInfo).port;
			const response = await fetch(`http://127.0.0.1:${bound}/api/snapshot`);
			expect(response.status).toBe(200);
			expect(await response.json()).toEqual({ path: "/api/snapshot" });
		} finally {
			await vite?.close();
			await closeServer(upstream);
		}
	}, 60_000);

	it("R35: a fresh load of the page uses the light theme", async () => {
		// A fresh load never consults the OS preference or saved state.
		expect(DEFAULT_THEME).toBe("light");
		expect(appSource).not.toMatch(/prefers-color-scheme/);
		expect(appSource).not.toMatch(/localStorage|sessionStorage/);

		// Even when the OS prefers dark, applying the default stays light.
		vi.stubGlobal(
			"matchMedia",
			vi.fn().mockReturnValue({
				matches: true,
				media: "(prefers-color-scheme: dark)",
				addEventListener: () => {},
				removeEventListener: () => {},
				addListener: () => {},
				removeListener: () => {},
			}),
		);
		applyTheme(DEFAULT_THEME);

		const root = document.documentElement;
		expect(root.classList.contains("dark")).toBe(false);
		expect(root.dataset.theme).toBe("light");
		expect(root.style.colorScheme).toBe("light");

		// The component renders the shell with the theme control.
		expect(appSource).toContain('data-act="theme"');
		if (await tryMountApp()) {
			expect(document.documentElement.classList.contains("dark")).toBe(false);
			expect(document.documentElement.dataset.theme).toBe("light");
			expect(document.querySelector("[data-act='theme']")).toBeTruthy();
		}
	});

	it("R36: a theme control switches the document between dark and light", async () => {
		// The component wires its control to the theme module.
		expect(appSource).toContain('data-act="theme"');
		expect(appSource).toMatch(/toggle\(/);
		expect(appSource).toMatch(/applyTheme\(/);

		const root = document.documentElement;
		let theme: Theme = DEFAULT_THEME;
		applyTheme(theme);
		expect(root.classList.contains("dark")).toBe(false);

		// Activating the control once goes dark, twice returns to light.
		theme = toggle(theme);
		applyTheme(theme);
		expect(root.classList.contains("dark")).toBe(true);
		expect(root.dataset.theme).toBe("dark");
		expect(root.style.colorScheme).toBe("dark");

		theme = toggle(theme);
		applyTheme(theme);
		expect(root.classList.contains("dark")).toBe(false);
		expect(root.dataset.theme).toBe("light");
		expect(root.style.colorScheme).toBe("light");

		// When the Svelte plugin is available, click the real control too.
		if (await tryMountApp()) {
			const control =
				document.querySelector<HTMLButtonElement>("[data-act='theme']");
			expect(control, "the theme control must render").toBeTruthy();
			expect(control?.getAttribute("role")).toBe("switch");
			expect(document.documentElement.classList.contains("dark")).toBe(false);

			control!.click();
			flushSync();
			expect(document.documentElement.classList.contains("dark")).toBe(true);
			expect(document.documentElement.dataset.theme).toBe("dark");

			control!.click();
			flushSync();
			expect(document.documentElement.classList.contains("dark")).toBe(false);
			expect(document.documentElement.dataset.theme).toBe("light");
		}
	});
});
