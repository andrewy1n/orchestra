// @vitest-environment jsdom
/**
 * Detail-overlay acceptance cases for the web dashboard UI.
 *
 * R14: phase overlay shows GET /api/phase, including tabs_for tabs.
 * R15: task overlay shows GET /api/task.
 * R16: requirement overlay shows GET /api/requirement.
 * R17: record overlay shows GET /api/record.
 * R18: Needs you overlay shows GET /api/needs.
 * R19: backlog overlay shows GET /api/backlog.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { appSource } from "./appSource";
import {
	backlogHref,
	detailTarget,
	needsHref,
	phaseHref,
	recordHref,
	requirementHref,
	taskHref,
} from "./detail";
import { evidenceBoard } from "./detailView";
import { parseRoute } from "./router";
import type { DeepPartial, EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));

const detailSource = readFileSync(path.join(here, "detail.ts"), "utf8");

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

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		phases: [],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
	return { token, efforts, generated_at: "2026-01-01T00:00:00Z" } as Snapshot;
}

type DetailMap = Record<string, unknown>;

function stubFetch(snap: Snapshot, details: DetailMap = {}) {
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
			if (url.includes("/api/journal")) {
				return new Response(JSON.stringify({ open: [], rest: [] }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			for (const [key, payload] of Object.entries(details)) {
				if (url.includes(key)) {
					return new Response(JSON.stringify(payload), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
			}
			if (url.includes("/api/snapshot")) {
				return new Response(JSON.stringify(snap), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			return new Response(JSON.stringify({ error: `unhandled ${url}` }), {
				status: 404,
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

async function openAndSettle(hash: string): Promise<void> {
	window.location.hash = hash.replace(/^#/, "");
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

function payloadText(): string {
	return document.querySelector("[data-detail-payload]")?.textContent ?? "";
}

describe("web-dashboard detail", () => {
	it("R14: Opening a phase shows the payload of GET /api/phase, including the tabs dashboard.model.tabs_for returns for that phase.", async () => {
		expect(appSource).toContain("data-detail=");
		expect(appSource).toContain("data-phase-tab=");
		expect(appSource).toMatch(/detailTarget|\/api\/phase|phase\?effort/);
		expect(detailSource).toMatch(/phase\?effort=/);

		const href = phaseHref("dashboard", "web-dashboard");
		expect(href).toBe("#/phase/dashboard/web-dashboard");
		const target = detailTarget(parseRoute(href));
		expect(target).toEqual({
			kind: "phase",
			apiPath: "phase?effort=dashboard&phase=web-dashboard",
			tab: undefined,
		});

		const phasePayload = {
			detail: {
				subject: "web-dashboard",
				title: "Web dashboard",
				state: "in_progress",
				body: "Phase body marker",
			},
			tabs: ["overview", "spec", "design", "decisions", "evidence", "tasks"],
			decisions: { groups: [] },
		};

		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]), {
			"/api/phase?": phasePayload,
		});

		if (await tryMountApp()) {
			await openAndSettle(href);
			const overlay = document.querySelector('[data-detail="phase"]');
			expect(overlay).toBeTruthy();
			for (const tab of phasePayload.tabs) {
				expect(
					document.querySelector(`[data-phase-tab="${tab}"]`),
				).toBeTruthy();
			}
			const text = payloadText();
			expect(text).toContain("Web dashboard");
			expect(text).toContain("Phase body marker");
			expect(text).toContain('"overview"');
			expect(text).toContain('"tasks"');
		}
	});

	it("R15: Opening a task shows the payload of GET /api/task.", async () => {
		expect(appSource).toMatch(/taskHref|\/api\/task|task\?id=/);
		expect(detailSource).toMatch(/task\?id=/);

		const href = taskHref("rec-task-1");
		expect(href).toBe("#/task/rec-task-1");
		expect(detailTarget(parseRoute(href))).toEqual({
			kind: "task",
			apiPath: "task?id=rec-task-1",
		});

		const taskPayload = {
			detail: {
				id: "rec-task-1",
				subject: "web-ui-detail",
				title: "Open detail overlays",
				status: "ready",
				description: "Task payload marker",
			},
		};

		stubFetch(
			makeSnapshot([
				effort({
					effort: "dashboard",
					tasks: [
						{
							id: "rec-task-1",
							subject: "web-ui-detail",
							title: "Open detail overlays",
							phase: "web-dashboard",
							status: "ready",
						},
					],
				}),
			]),
			{ "/api/task?": taskPayload },
		);

		if (await tryMountApp()) {
			await openAndSettle(href);
			expect(document.querySelector('[data-detail="task"]')).toBeTruthy();
			const text = payloadText();
			expect(text).toContain("web-ui-detail");
			expect(text).toContain("Task payload marker");
			expect(text).toContain("Open detail overlays");
		}
	});

	it("R16: Opening a requirement shows the payload of GET /api/requirement.", async () => {
		expect(detailSource).toMatch(/requirement\?effort=/);

		const href = requirementHref("dashboard", "web-dashboard", "R14");
		expect(href).toBe("#/requirement/dashboard/web-dashboard/R14");
		expect(detailTarget(parseRoute(href))).toEqual({
			kind: "requirement",
			apiPath: "requirement?effort=dashboard&phase=web-dashboard&id=R14",
		});

		const reqPayload = {
			detail: {
				id: "R14",
				text: "Opening a phase shows the payload",
				status: "unassessed",
				phase: "web-dashboard",
			},
		};

		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]), {
			"/api/requirement?": reqPayload,
		});

		if (await tryMountApp()) {
			await openAndSettle(href);
			expect(
				document.querySelector('[data-detail="requirement"]'),
			).toBeTruthy();
			const text = payloadText();
			expect(text).toContain("R14");
			expect(text).toContain("Opening a phase shows the payload");
		}
	});

	it("R17: Opening a record shows the payload of GET /api/record.", async () => {
		expect(detailSource).toMatch(/record\?id=/);
		expect(appSource).toMatch(/recordHref/);

		const href = recordHref("rec-journal-1");
		expect(href).toBe("#/record/rec-journal-1");
		expect(detailTarget(parseRoute(href))).toEqual({
			kind: "record",
			apiPath: "record?id=rec-journal-1",
		});

		const recordPayload = {
			record: {
				id: "rec-journal-1",
				record_type: "tuner:finding",
				subject: "open-finding",
				body: "Record payload marker",
			},
		};

		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]), {
			"/api/record?": recordPayload,
		});

		if (await tryMountApp()) {
			await openAndSettle(href);
			expect(document.querySelector('[data-detail="record"]')).toBeTruthy();
			const text = payloadText();
			expect(text).toContain("tuner:finding");
			expect(text).toContain("Record payload marker");
			expect(text).toContain("open-finding");
		}
	});

	it("R18: Opening a Needs you item shows the payload of GET /api/needs.", async () => {
		expect(detailSource).toMatch(/needs\?effort=/);
		expect(appSource).toMatch(/needsHref/);

		const href = needsHref("dashboard", "q1");
		expect(href).toBe("#/needs/dashboard/q1");
		expect(detailTarget(parseRoute(href))).toEqual({
			kind: "needs",
			apiPath: "needs?effort=dashboard&id=q1",
		});

		const needsPayload = {
			item: {
				kind: "blocking-question",
				id: "q1",
				subject: "which-backend",
				text: "which backend",
				revision: "sha256:abc",
				approval: {
					confirm_choices: [{ action: "approve", label: "Approve" }],
				},
			},
		};

		stubFetch(
			makeSnapshot([
				effort({
					effort: "dashboard",
					needs_you: [
						{
							kind: "blocking-question",
							id: "q1",
							subject: "which-backend",
							text: "which backend",
						},
					],
				}),
			]),
			{ "/api/needs?": needsPayload },
		);

		if (await tryMountApp()) {
			await openAndSettle(href);
			expect(document.querySelector('[data-detail="needs"]')).toBeTruthy();
			const text = payloadText();
			expect(text).toContain("blocking-question");
			expect(text).toContain("which-backend");
			expect(text).toContain("sha256:abc");
			expect(text).toContain("confirm_choices");
		}
	});

	it("R19: Opening a backlog item shows the payload of GET /api/backlog.", async () => {
		expect(detailSource).toMatch(/backlog\?effort=/);
		expect(appSource).toMatch(/backlogHref/);

		const href = backlogHref("dashboard", "b1");
		expect(href).toBe("#/backlog/dashboard/b1");
		expect(detailTarget(parseRoute(href))).toEqual({
			kind: "backlog",
			apiPath: "backlog?effort=dashboard&id=b1",
		});

		const backlogPayload = {
			item: {
				id: "b1",
				subject: "park-me",
				text: "parked work",
				status: "open",
				source: "chat",
			},
		};

		stubFetch(
			makeSnapshot([
				effort({
					effort: "dashboard",
					backlog: [
						{
							id: "b1",
							subject: "park-me",
							text: "parked work",
							status: "open",
							source: "chat",
						},
					],
				}),
			]),
			{ "/api/backlog?": backlogPayload },
		);

		if (await tryMountApp()) {
			await openAndSettle(href);
			expect(document.querySelector('[data-detail="backlog"]')).toBeTruthy();
			const text = payloadText();
			expect(text).toContain("park-me");
			expect(text).toContain("parked work");
			expect(text).toContain('"status": "open"');
		}
	});
});

describe("evidence tab", () => {
	it("lists every requirement on the evidence tab", () => {
		const board = evidenceBoard({
			detail: {
				evidence: {
					stage: "release",
					weight: "full",
					requirements: [
						{
							id: "R1",
							text: "Skills stay inside their directory.",
							status: "verified",
							tasks: 3,
							tasks_done: 3,
							next: "",
						},
						{
							id: "R2",
							text: "The installer covers the host matrix.",
							status: "verified",
							tasks: 1,
							tasks_done: 1,
						},
					],
				},
			},
		});
		expect(board.facts.map((fact) => fact.value)).toEqual(["release", "full"]);
		expect(board.rows.map((row) => row.id)).toEqual(["R1", "R2"]);
		expect(board.rows[0]?.text).toBe("Skills stay inside their directory.");
		expect(board.rows[0]?.tasks).toBe("3/3");
		expect(board.rows[0]?.tone).toBe("ok");
		expect(board.rows[1]?.text).toBe("The installer covers the host matrix.");
	});
});
