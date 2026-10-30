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

function phase(
	subject: string,
	title: string,
	ordinal: number,
	state: string,
): EffortView["phases"][number] {
	return {
		subject,
		title,
		ordinal,
		state,
		done: 0,
		total: 0,
	} as EffortView["phases"][number];
}

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
		effort({
			effort: "invoicing",
			area: "billing",
			phases: [
				phase("draft", "Draft invoices", 1, "in_progress"),
				phase("send", "Send invoices", 2, "planned"),
				phase("remind", "Remind payers", 3, "planned"),
			],
		}),
		effort({
			effort: "web",
			phases: [phase("launch", "Launch", 1, "in_progress")],
		}),
		effort({
			effort: "ledger",
			area: "billing",
			phases: [
				phase("l1", "Ledger one", 1, "done"),
				phase("l2", "Ledger two", 2, "done"),
				phase("l3", "Ledger three", 3, "done"),
				phase("l4", "Ledger four", 4, "in_progress"),
				phase("l5", "Ledger five", 5, "planned"),
			],
		}),
	],
} as Snapshot;

const areas: AreasResponse = [
	{ subject: "billing", title: "Billing", scope: "", open_count: 0, ideas: [] },
];

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function phasePayload(effortName: string, subject: string) {
	const row = snapshot.efforts
		.find((view) => view.effort === effortName)
		?.phases.find((item) => item.subject === subject);
	return {
		tabs: ["overview", "spec"],
		detail: {
			subject,
			title: row?.title ?? subject,
			effort: effortName,
			state: row?.state ?? "planned",
			body: "Phase notes body",
			tasks: [],
		},
	};
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
			if (url.includes("/api/phase")) {
				const query = new URL(url, "http://localhost").searchParams;
				return json(
					phasePayload(query.get("effort") ?? "", query.get("phase") ?? ""),
				);
			}
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

function railItems(): HTMLElement[] {
	return [
		...document.querySelectorAll<HTMLElement>("nav.rail [data-rail-item]"),
	];
}

function railKeys(): string[] {
	return railItems().map((el) => el.getAttribute("data-rail-item") ?? "");
}

describe("phase page navigation", () => {
	it("R2 an effort with an area gives the breadcrumb Product, area, effort, phase", async () => {
		await mountApp("#/phase/invoicing/send");
		expect(crumbText()).toBe("Product › Billing › invoicing › Send invoices");
	});

	it("R3 an effort with no area gives the breadcrumb Product, effort, phase", async () => {
		await mountApp("#/phase/web/launch");
		expect(crumbText()).toBe("Product › web › Launch");
	});

	it("R18 the left rail lists the phases of the effort", async () => {
		await mountApp("#/phase/invoicing/send");
		expect(railKeys()).toEqual(["draft", "send", "remind"]);
		expect(
			railItems().map((el) => el.querySelector(".name")?.textContent?.trim()),
		).toEqual(["Draft invoices", "Send invoices", "Remind payers"]);
		expect(railItems().map((el) => el.getAttribute("href"))).toEqual([
			"#/phase/invoicing/draft",
			"#/phase/invoicing/send",
			"#/phase/invoicing/remind",
		]);
	});

	it("R19 the left rail marks the current phase", async () => {
		await mountApp("#/phase/invoicing/send");
		const current = railItems().filter(
			(el) => el.getAttribute("aria-current") === "page",
		);
		expect(current.map((el) => el.getAttribute("data-rail-item"))).toEqual([
			"send",
		]);
	});

	it("R20 the left rail folds older done phases behind a button that shows them", async () => {
		await mountApp("#/phase/ledger/l4");
		const button = document.querySelector<HTMLButtonElement>(
			'nav.rail [data-act="show-done-phases"]',
		);
		expect(button).not.toBeNull();
		const folded = railKeys();
		expect(folded).toContain("l4");
		expect(folded).toContain("l5");
		expect(folded).not.toContain("l1");
		expect(folded.length).toBeLessThan(5);
		button!.click();
		await settle();
		expect(railKeys()).toEqual(["l1", "l2", "l3", "l4", "l5"]);
	});

	it("R28 Esc on the phase page opens the effort page", async () => {
		await mountApp("#/phase/invoicing/send");
		expect(document.querySelector("main [data-phase-page]")).not.toBeNull();
		(document.activeElement ?? document.body).dispatchEvent(
			new KeyboardEvent("keydown", {
				key: "Escape",
				bubbles: true,
				cancelable: true,
			}),
		);
		await settle();
		expect(window.location.hash).toBe("#/effort/invoicing");
		expect(document.querySelector("main [data-phase-page]")).toBeNull();
		expect(document.querySelector("main [data-effort-title]")).not.toBeNull();
	});
});
