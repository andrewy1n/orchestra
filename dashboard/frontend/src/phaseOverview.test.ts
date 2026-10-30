// @vitest-environment jsdom
/**
 * Phase overlay chrome on every tab (phase-overview).
 */

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { appSource } from "./appSource";
import { buildPhaseChrome } from "./phaseChrome";
import type { DeepPartial, EffortView, Snapshot } from "./types";

let mounted: ReturnType<typeof mount> | undefined;

function resetDocument() {
	if (mounted) {
		unmount(mounted);
		mounted = undefined;
	}
	document.body.innerHTML = "";
}

beforeEach(() => {
	resetDocument();
	window.location.hash = "";
	vi.useFakeTimers();
});

afterEach(() => {
	resetDocument();
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

const phasePayload = {
	tabs: ["overview", "spec", "design", "tasks", "evidence"],
	detail: {
		subject: "phase-overview",
		title: "Phase overview UI",
		effort: "dashboard",
		state: "in_progress",
		body: "Phase notes body",
		spec_body: "## Requirements\n\nR1: chrome",
		design_body: "## Architecture\n\nShared chrome",
		awaiting_signoff: false,
		position: "Ship shared chrome",
		tasks: [
			{ id: "t1", subject: "t1", title: "Chrome", status: "done", wave: 1 },
			{ id: "t2", subject: "t2", title: "Tabs", status: "ready", wave: 1 },
			{ id: "t3", subject: "t3", title: "Verify", status: "ready", wave: 2 },
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

const emptyPhasePayload = {
	tabs: ["overview", "spec"],
	detail: {
		subject: "plain",
		title: "Plain",
		effort: "dashboard",
		state: "planned",
		body: "",
		tasks: [],
	},
};

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		phases: [
			{
				subject: "phase-overview",
				title: "Phase overview UI",
				ordinal: 1,
				state: "in_progress",
				done: 1,
				total: 3,
			},
		],
		tasks: [],
		needs_you: [],
		backlog: [],
		position: "Continue phase-overview",
		...partial,
	} as EffortView;
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
	return { token, efforts, generated_at: "2026-01-01T00:00:00Z" } as Snapshot;
}

function stubFetch(snap: Snapshot, phaseByKey: Record<string, unknown> = {}) {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) {
				return new Response(JSON.stringify({ token: snap.token }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			if (url.includes("/api/phase")) {
				const match = /[?&]phase=([^&]+)/.exec(url);
				const name = match ? decodeURIComponent(match[1]!) : "";
				const data = phaseByKey[name] ?? phasePayload;
				return new Response(JSON.stringify(data), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			if (url.includes("/api/requirement")) {
				return new Response(
					JSON.stringify({
						detail: {
							id: "R1",
							text: "chips",
							status: "open",
							phase: "phase-overview",
						},
					}),
					{ status: 200, headers: { "content-type": "application/json" } },
				);
			}
			return new Response(JSON.stringify(snap), {
				status: 200,
				headers: { "content-type": "application/json" },
			});
		}),
	);
}

async function tryMountApp(): Promise<boolean> {
	try {
		const module = await import("./App.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		return true;
	} catch {
		mounted = undefined;
		return false;
	}
}

async function openPhase(tab = "overview") {
	const hash =
		tab === "overview"
			? "#/phase/dashboard/phase-overview"
			: `#/phase/dashboard/phase-overview/tab/${tab}`;
	window.location.hash = hash;
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

describe("buildPhaseChrome", () => {
	it("R1: status chips include lifecycle and task done/total", () => {
		const chrome = buildPhaseChrome(phasePayload);
		const labels = chrome.chips.map((c) => c.label);
		expect(labels.some((l) => /in progress/i.test(l))).toBe(true);
		expect(labels).toContain("1/3 tasks");
	});

	it("R2: progress cue for phase tasks", () => {
		const chrome = buildPhaseChrome(phasePayload);
		expect(chrome.progressLabel).toMatch(/1 of 3/);
	});

	it("R3: next-action from detail or fallback", () => {
		expect(buildPhaseChrome(phasePayload).nextAction).toBe(
			"Ship shared chrome",
		);
		expect(
			buildPhaseChrome(emptyPhasePayload, { position: "From snapshot" })
				.nextAction,
		).toBe("From snapshot");
	});

	it("R4: requirements strip when evidence present", () => {
		const chrome = buildPhaseChrome(phasePayload);
		expect(chrome.requirements.map((r) => r.id)).toEqual(["R1", "R5"]);
		expect(chrome.requirements[0]?.status).toBe("pass");
	});

	it("R6: compact per-wave summary", () => {
		const chrome = buildPhaseChrome(phasePayload);
		expect(chrome.waves).toEqual([
			{ wave: "1", total: 2, done: 1 },
			{ wave: "2", total: 1, done: 0 },
		]);
	});

	it("R8: empty states when no spec/evidence/tasks", () => {
		const chrome = buildPhaseChrome(emptyPhasePayload);
		expect(chrome.requirements).toEqual([]);
		expect(chrome.waves).toEqual([]);
		expect(chrome.progressLabel).toMatch(/no tasks/i);
		expect(chrome.chips.some((c) => c.label.includes("0/0"))).toBe(true);
	});
});

describe("phase overlay UI", () => {
	it("wires shared chrome for every phase tab", () => {
		expect(appSource).toMatch(/buildPhaseChrome/);
		expect(appSource).toMatch(/data-phase-chrome/);
		expect(appSource).toMatch(/data-phase-reqs/);
	});

	it("R1 R2 R3 R4 R6: chrome renders on Overview", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openPhase("overview");
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		expect(document.querySelector("[data-phase-chips]")?.textContent).toMatch(
			/in progress/i,
		);
		expect(document.querySelector("[data-phase-chips]")?.textContent).toMatch(
			/1\/3 tasks/,
		);
		expect(document.querySelector("[data-phase-progress]")).toBeNull();
		expect(document.querySelector("[data-phase-next]")?.textContent).toContain(
			"Ship shared chrome",
		);
		expect(document.querySelector('[data-phase-req="R1"]')).toBeTruthy();
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		expect(document.querySelector("[data-phase-waves]")).toBeNull();
	});

	it("R1: chrome also renders on Spec (not Overview-only)", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openPhase("spec");
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		expect(
			document
				.querySelector('[data-phase-tab="spec"]')
				?.getAttribute("aria-selected"),
		).toBe("true");
		expect(
			document.querySelector("[data-detail-section]")?.textContent,
		).toMatch(/Specification|Requirements/i);
	});

	it("R5: activating a requirement chip opens the requirement overlay", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openPhase("spec");
		const btn = document.querySelector('[data-phase-req="R1"]');
		expect(btn).toBeTruthy();
		btn!.dispatchEvent(
			new MouseEvent("click", { bubbles: true, cancelable: true }),
		);
		flushSync();
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(window.location.hash).toContain(
			"#/requirement/dashboard/phase-overview/R1",
		);
	});

	it("R7: tab bodies use section cards rather than bare dumps only", async () => {
		expect(appSource).toMatch(/section-card|data-section-card/);
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openPhase("tasks");
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		const body = document.querySelector("[data-task-board]");
		expect(body?.querySelector("[data-phase-task]")).toBeTruthy();
		expect(body?.textContent).toMatch(/Chrome/);
		expect(body?.textContent).toMatch(/Tabs/);
	});

	it("R9: tab-specific content remains under shared chrome", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openPhase("design");
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		expect(
			document.querySelector('[data-detail-section="Design"]')?.textContent,
		).toMatch(/Architecture|Shared chrome/i);
	});

	it("R8: chrome empty states without dumping JSON", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]), {
			"phase-overview": emptyPhasePayload,
		});
		if (!(await tryMountApp())) return;
		await openPhase("overview");
		expect(document.querySelector("[data-phase-chrome]")).toBeTruthy();
		expect(document.querySelector("[data-phase-reqs-empty]")).toBeTruthy();
		expect(document.body.textContent).not.toMatch(/"detail"\s*:/);
	});
});
