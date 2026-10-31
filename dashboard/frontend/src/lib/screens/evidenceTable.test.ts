// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

const phasePayload = {
	tabs: ["overview", "evidence"],
	detail: {
		subject: "phase-overview",
		title: "Phase overview UI",
		effort: "dashboard",
		state: "in_progress",
		body: "Phase notes body",
		tasks: [],
		evidence: {
			stage: "verify",
			weight: "full",
			requirements: [
				{
					id: "R1",
					text: "chips",
					status: "open",
					tasks: 2,
					tasks_done: 1,
					next: "run verify",
					latest_check: { result: "pass" },
				},
				{
					id: "R5",
					text: "nav",
					status: "open",
					latest_check: { result: "fail" },
				},
			],
		},
	},
};

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "",
		phases: [
			{
				subject: "phase-overview",
				title: "Phase overview UI",
				ordinal: 1,
				state: "in_progress",
				done: 1,
				total: 2,
			},
		],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [effort({ effort: "dashboard" })],
} as Snapshot;

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
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/phase")) return json(phasePayload);
			if (url.includes("/api/requirement")) {
				return json({
					detail: {
						id: "R1",
						text: "chips",
						status: "open",
						phase: "phase-overview",
					},
				});
			}
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

const PAGE = "#/phase/dashboard/phase-overview/tab/evidence";
const REQUIREMENT_HASH = "#/requirement/dashboard/phase-overview/R1";

function table(): HTMLElement | null {
	return document.querySelector<HTMLElement>(
		"main [data-evidence-board] table[data-evidence-reqs]",
	);
}

function row(id: string): HTMLElement | null {
	return document.querySelector<HTMLElement>(
		`main [data-evidence-board] [data-evidence-reqs] [data-evidence-req="${id}"]`,
	);
}

function requirementDialog(): Element | null {
	return document.querySelector('[role="dialog"][data-detail="requirement"]');
}

describe("evidence table", () => {
	it("R12 the evidence tab lists requirements in a shadcn table", async () => {
		await mountApp(PAGE);
		const found = table();
		expect(found).not.toBeNull();
		expect(found?.getAttribute("data-slot")).toBe("table");
		const rows = found?.querySelectorAll<HTMLElement>(
			"tbody [data-evidence-req]",
		);
		expect([...(rows ?? [])].map((el) => el.dataset.evidenceReq)).toEqual([
			"R1",
			"R5",
		]);
		for (const item of rows ?? []) {
			expect(item.tagName).toBe("TR");
			expect(item.getAttribute("data-slot")).toBe("table-row");
		}
	});

	it("R13 the evidence table has the column headers Req, Status, Tasks and Summary", async () => {
		await mountApp(PAGE);
		const headers = [...(table()?.querySelectorAll("thead th") ?? [])].map(
			(el) => el.textContent?.trim(),
		);
		expect(headers).toEqual(["Req", "Status", "Tasks", "Summary"]);
		const first = row("R1");
		expect(first?.textContent).toContain("1/2");
		expect(first?.textContent).toContain("chips");
		expect(first?.textContent).toContain("next run verify");
	});

	it("R14 a click on an evidence row opens the requirement overlay", async () => {
		await mountApp(PAGE);
		expect(requirementDialog()).toBeNull();
		const target = row("R1");
		expect(target).not.toBeNull();
		target?.click();
		await settle();
		expect(window.location.hash).toBe(REQUIREMENT_HASH);
		expect(requirementDialog()).not.toBeNull();
	});

	it("R15 Enter on a focused evidence row opens the requirement overlay", async () => {
		await mountApp(PAGE);
		const target = row("R1");
		expect(target?.getAttribute("role")).toBe("button");
		expect(target?.getAttribute("tabindex")).toBe("0");
		target?.dispatchEvent(
			new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
		);
		await settle();
		expect(window.location.hash).toBe(REQUIREMENT_HASH);
		expect(requirementDialog()).not.toBeNull();
	});

	it("R15 Space on a focused evidence row opens the requirement overlay without scrolling", async () => {
		await mountApp(PAGE);
		const target = row("R1");
		const event = new KeyboardEvent("keydown", {
			key: " ",
			bubbles: true,
			cancelable: true,
		});
		target?.dispatchEvent(event);
		await settle();
		expect(event.defaultPrevented).toBe(true);
		expect(window.location.hash).toBe(REQUIREMENT_HASH);
		expect(requirementDialog()).not.toBeNull();
	});
});
