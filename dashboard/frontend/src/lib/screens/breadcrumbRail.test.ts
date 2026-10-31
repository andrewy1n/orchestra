// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import type { DeepPartial, EffortView, Snapshot } from "../../types";

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

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "",
		phases: [],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [
		effort({ effort: "invoicing", area: "billing" }),
		effort({ effort: "refunds", area: "billing" }),
		effort({ effort: "old-billing", area: "billing", finished: true }),
		effort({ effort: "web" }),
		effort({ effort: "tooling" }),
	],
} as Snapshot;

function area(subject: string, title: string): AreasResponse[number] {
	return {
		subject,
		title,
		scope: "",
		open_count: 0,
		ideas: [],
	};
}

const areas: AreasResponse = [area("billing", "Billing"), area("ops", "Ops")];

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

async function mountApp(hash: string) {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json(areas);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function crumbText(): string {
	return (
		document
			.querySelector("[data-breadcrumb]")
			?.textContent?.replace(/\s+/g, " ")
			.trim() ?? ""
	);
}

function railLabels(): string[] {
	return [...document.querySelectorAll("[data-rail-item]")].map(
		(el) => el.querySelector(".name")?.textContent?.trim() ?? "",
	);
}

describe("breadcrumb and rail", () => {
	it("R9 the product index has no left rail", async () => {
		await mountApp("");
		expect(document.querySelector("main")).not.toBeNull();
		expect(document.querySelector("nav.rail")).toBeNull();
		expect(document.querySelector("[data-rail-item]")).toBeNull();
	});

	it("R20 the area page breadcrumb reads Product then the area title", async () => {
		await mountApp("#/area/billing");
		expect(crumbText()).toBe("Product › Billing");
	});

	it("R21 an effort with an area breadcrumb reads Product, area title, effort", async () => {
		await mountApp("#/effort/invoicing");
		expect(crumbText()).toBe("Product › Billing › invoicing");
	});

	it("R22 an effort with no area breadcrumb reads Product then the effort", async () => {
		await mountApp("#/effort/web");
		expect(crumbText()).toBe("Product › web");
	});

	it("R23 every breadcrumb part except the last is a link", async () => {
		await mountApp("#/effort/invoicing");
		const nav = document.querySelector("[data-breadcrumb]")!;
		const links = [...nav.querySelectorAll("a")];
		expect(links.map((a) => a.textContent?.trim())).toEqual([
			"Product",
			"Billing",
		]);
		expect(links.map((a) => a.getAttribute("href"))).toEqual([
			"#/",
			"#/area/billing",
		]);
		const last = nav.querySelector("[aria-current='page']");
		expect(last?.tagName).toBe("SPAN");
		expect(last?.textContent?.trim()).toBe("invoicing");
		expect(nav.querySelectorAll("a, [aria-current='page']")).toHaveLength(3);
	});

	it("R24 the area page rail lists the areas", async () => {
		await mountApp("#/area/billing");
		const rail = document.querySelector("nav.rail");
		expect(rail?.getAttribute("data-rail-level")).toBe("area");
		expect(railLabels()).toEqual(["Billing", "Ops"]);
		const items = [...document.querySelectorAll("[data-rail-item]")];
		expect(items.map((el) => el.getAttribute("href"))).toEqual([
			"#/area/billing",
			"#/area/ops",
		]);
		expect(items.map((el) => el.classList.contains("on"))).toEqual([
			true,
			false,
		]);
	});

	it("R25 the effort page rail lists the efforts of the same area", async () => {
		await mountApp("#/effort/invoicing");
		expect(
			document.querySelector("nav.rail")?.getAttribute("data-rail-level"),
		).toBe("effort");
		expect(railLabels()).toEqual(["invoicing", "refunds"]);
		unmount(mounted!);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountApp("#/effort/web");
		expect(railLabels()).toEqual(["web", "tooling"]);
	});

	it("R26 the effort rail show-finished toggle reveals hidden finished efforts", async () => {
		await mountApp("#/effort/invoicing");
		const toggle = document.querySelector<HTMLButtonElement>(
			'[data-act="show-finished"]',
		)!;
		expect(toggle.textContent?.trim()).toBe("1 finished");
		expect(railLabels()).not.toContain("old-billing");
		toggle.click();
		await settle();
		expect(railLabels()).toEqual(["invoicing", "refunds", "old-billing"]);
		expect(toggle.textContent?.trim()).toBe("Hide finished");
	});
});
