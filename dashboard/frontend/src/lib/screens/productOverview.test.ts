// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ProductResponse } from "../../api-types";

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	document.body.innerHTML = "";
	window.location.hash = "";
	vi.useFakeTimers();
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	document.body.innerHTML = "";
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

const overview: ProductResponse = {
	statement: { purpose: "Keep work verifiable.", audience: "Agent teams." },
	capabilities: [
		{
			subject: "live-roadmap",
			title: "Live roadmap",
			description: "Shows work as it stands.",
			status: "current",
		},
	],
	goals: [
		{
			subject: "export",
			title: "Export",
			description: "Share the roadmap as a file.",
			status: "planned",
		},
	],
};

const empty: ProductResponse = { statement: null, capabilities: [], goals: [] };

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountApp(body: ProductResponse) {
	const snapshot = {
		token: "tok-1",
		generated_at: "2026-01-01T00:00:00Z",
		efforts: [],
	};
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: "tok-1" });
			if (url.includes("/api/product")) return json(body);
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	window.location.hash = "#/areas";
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function text(selector: string): string | undefined {
	return document.querySelector(selector)?.textContent?.trim();
}

describe("product overview", () => {
	it("R7 shows the statement, capabilities and goals above the areas", async () => {
		await mountApp(overview);
		expect(text("[data-statement-purpose]")).toBe("Keep work verifiable.");
		expect(text("[data-statement-audience]")).toBe("Agent teams.");
		const capability = document.querySelector(
			'[data-product-section="capabilities"] [data-product-item="live-roadmap"]',
		);
		expect(capability?.querySelector("[data-item-status]")?.textContent).toBe(
			"current",
		);
		expect(
			capability?.querySelector("[data-item-description]")?.textContent,
		).toBe("Shows work as it stands.");
		const goal = document.querySelector(
			'[data-product-section="goals"] [data-product-item="export"]',
		);
		expect(goal?.querySelector("[data-item-status]")?.textContent).toBe(
			"planned",
		);
		const block = document.querySelector("[data-product-overview]");
		const heading = document.querySelector("[data-product-index] h1");
		expect(
			(block as Node).compareDocumentPosition(heading as Node) &
				Node.DOCUMENT_POSITION_FOLLOWING,
		).toBeTruthy();
	});

	it("R7 says so when there is no statement", async () => {
		await mountApp(empty);
		expect(
			document.querySelector("[data-product-no-statement]"),
		).not.toBeNull();
		expect(document.querySelector("[data-statement-purpose]")).toBeNull();
	});
});
