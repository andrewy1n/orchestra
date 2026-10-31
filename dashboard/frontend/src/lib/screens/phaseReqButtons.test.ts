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
	tabs: ["overview", "spec", "tasks"],
	detail: {
		subject: "phase-overview",
		title: "Phase overview UI",
		effort: "dashboard",
		state: "in_progress",
		body: "Phase notes body",
		spec_body: "## Requirements\n\nR1: chrome",
		tasks: [
			{ id: "t1", subject: "t1", title: "Chrome", status: "done", wave: 1 },
			{ id: "t2", subject: "t2", title: "Tabs", status: "ready", wave: 1 },
		],
		evidence: {
			stage: "verify",
			weight: "full",
			requirements: [
				{
					id: "R1",
					text: "chips",
					status: "open",
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

const PAGE = "#/phase/dashboard/phase-overview";

function chips(): HTMLElement[] {
	return [...document.querySelectorAll<HTMLElement>("main [data-phase-req]")];
}

describe("requirement chips", () => {
	it("R17 each requirement chip is a shadcn button that keeps its data-phase-req attribute", async () => {
		await mountApp(PAGE);
		const found = chips();
		expect(found.map((el) => el.getAttribute("data-phase-req"))).toEqual([
			"R1",
			"R5",
		]);
		for (const chip of found) {
			expect(chip.tagName).toBe("BUTTON");
			expect(chip.getAttribute("data-slot")).toBe("button");
		}
	});

	it("R18 a click on a requirement chip opens the requirement overlay", async () => {
		await mountApp(PAGE);
		expect(document.querySelector('[role="dialog"]')).toBeNull();
		const chip = chips().find((el) => el.dataset.phaseReq === "R1");
		expect(chip).toBeDefined();
		chip!.click();
		await settle();
		expect(window.location.hash).toBe(
			"#/requirement/dashboard/phase-overview/R1",
		);
		const dialog = document.querySelector(
			'[role="dialog"][data-detail="requirement"]',
		);
		expect(dialog).not.toBeNull();
		expect(dialog?.textContent).toContain("chips");
	});
});
