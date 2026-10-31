// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import { areaHref, effortHref } from "../../detail";
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
		effort({ effort: "invoices", area: "billing", goal: "Send invoices" }),
		effort({ effort: "loose", area: "" }),
	],
} as Snapshot;

function idea(subject: string, text: string, status: string, effort: string) {
	return { subject, text, status, area: "billing", effort, phase: "" };
}

const billing = {
	subject: "billing",
	title: "Billing",
	scope: "Invoices.",
	open_count: 1,
	ideas: [
		idea("open-idea", "Open idea", "open", ""),
		idea("moved-idea", "Moved idea", "promoted", "invoices"),
		idea("other-moved", "Other moved idea", "promoted", "refunds"),
	],
};

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function stubFetch(areas: AreasResponse) {
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
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountAt(hash: string, areas: AreasResponse = [billing]) {
	stubFetch(areas);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

describe("started as efforts and area chip", () => {
	it("R12 the area page lists promoted ideas under Started as efforts", async () => {
		await mountAt(areaHref("billing"));
		const section = document.querySelector("[data-area-started]");
		expect(section).not.toBeNull();
		expect(section?.textContent).toContain("Started as efforts");
		expect(section?.textContent).toContain("Moved idea");
		expect(section?.textContent).toContain("Other moved idea");
		expect(section?.textContent).not.toContain("Open idea");
		const screen = document.querySelector("[data-area-screen]") as HTMLElement;
		expect(
			screen.querySelector("[data-area-open]")?.textContent ?? "",
		).not.toContain("Moved idea");
		expect(screen.querySelector("[data-effort-row] [data-idea]")).toBeNull();
		expect(screen.querySelectorAll("[data-effort-row]")).toHaveLength(1);
		unmount(mounted!);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountAt(areaHref("billing"), [
			{ ...billing, ideas: [idea("open-idea", "Open idea", "open", "")] },
		]);
		expect(document.querySelector("[data-area-screen]")).not.toBeNull();
		expect(document.querySelector("[data-area-started]")).toBeNull();
	});

	it("R13 each started line links to its effort", async () => {
		await mountAt(areaHref("billing"));
		const lines = [
			...document.querySelectorAll("a[data-started-effort]"),
		] as HTMLAnchorElement[];
		expect(
			lines.map((line) => line.getAttribute("data-started-effort")),
		).toEqual(["invoices", "refunds"]);
		expect(lines.map((line) => line.getAttribute("href"))).toEqual([
			effortHref("invoices"),
			effortHref("refunds"),
		]);
		expect(lines[0]?.textContent).toContain("Moved idea");
	});

	it("R19 the effort page shows an area chip linking to the area", async () => {
		await mountAt(effortHref("invoices"));
		const chip = document.querySelector(
			"a[data-area-chip]",
		) as HTMLAnchorElement | null;
		expect(chip).not.toBeNull();
		expect(chip?.classList.contains("area-chip")).toBe(true);
		expect(chip?.getAttribute("href")).toBe(areaHref("billing"));
		expect(chip?.textContent).toContain("Billing");
		unmount(mounted!);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountAt(effortHref("loose"));
		expect(document.querySelector("[data-effort-title]")).not.toBeNull();
		expect(document.querySelector("[data-area-chip]")).toBeNull();
	});
});
