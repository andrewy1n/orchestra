// @vitest-environment jsdom
/**
 * Calm home side rail + journal screen (side-rail-calm).
 *
 * R1: home side rail has no individual journal entry rows.
 * R2: Needs you and Backlog remain.
 * R3: repair/evaluate show one journal teaser with open count when known →
 *     navigates to journal screen.
 * R4: deliver/incidental show no teaser.
 * R5: hash route opens journal screen loading GET /api/journal for effort.
 * R6: lists open then earlier; each row type + subject/text.
 * R7: text filter by subject or text.
 * R8: activating row opens existing record detail overlay.
 * R9: Esc or back returns to effort home.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JournalResponse } from "./api-types";
import { journalHref } from "./detail";
import { parseRoute } from "./router";
import { filterJournal, orderedJournal } from "./side";
import type { DeepPartial, EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = readFileSync(path.join(here, "App.svelte"), "utf8");

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

function stubFetch(
	snap: Snapshot,
	journalByEffort: Record<string, DeepPartial<JournalResponse>> = {},
) {
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
				const match = /[?&]effort=([^&]+)/.exec(url);
				const name = match ? decodeURIComponent(match[1]!) : "";
				const data = journalByEffort[name] ?? { open: [], rest: [] };
				return new Response(JSON.stringify(data), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
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

describe("side-rail-home calm rail", () => {
	it("R1: home side rail has no individual journal entry rows", async () => {
		expect(appSource).not.toContain("data-side-journal>");
		expect(appSource).not.toMatch(/data-side-journal(?!-)/);

		const journal: DeepPartial<JournalResponse> = {
			open: [
				{
					id: "j1",
					record_type: "tuner:finding",
					subject: "open-finding",
					open: true,
				},
			],
			rest: [
				{
					id: "j2",
					record_type: "conductor:failed-attempt",
					subject: "closed",
					open: false,
				},
			],
		};
		stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
			alpha: journal,
		});
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		expect(document.querySelectorAll("[data-journal]").length).toBe(0);
		expect(document.querySelector('[data-journal="j1"]')).toBeNull();
		expect(document.querySelector('[data-journal="j2"]')).toBeNull();
	});

	it("R2: Needs you and Backlog remain", async () => {
		expect(appSource).toContain("data-side-needs");
		expect(appSource).toContain("data-side-backlog");

		const alpha = effort({
			effort: "alpha",
			kind: "deliver",
			needs_you: [
				{
					kind: "blocking-question",
					id: "q1",
					subject: "decide",
					text: "which?",
				},
			],
			backlog: [
				{
					id: "b1",
					subject: "park",
					text: "later",
					status: "open",
				},
			],
		});
		stubFetch(makeSnapshot([alpha]));
		if (!(await tryMountApp())) return;

		expect(document.querySelector("[data-side-needs]")).toBeTruthy();
		expect(document.querySelector('[data-needs="q1"]')).toBeTruthy();
		expect(document.querySelector("[data-side-backlog]")).toBeTruthy();
		expect(document.querySelector('[data-backlog="b1"]')).toBeTruthy();
	});

	it("R3: repair/evaluate show one journal teaser with open count when known → navigates to journal screen", async () => {
		expect(appSource).toContain("data-journal-teaser");
		expect(appSource).toMatch(/journalHref/);

		const journal: DeepPartial<JournalResponse> = {
			open: [
				{
					id: "j-open",
					record_type: "tuner:finding",
					subject: "find-me",
					open: true,
				},
				{
					id: "j-open-2",
					record_type: "score:continuity-question",
					subject: "ask",
					open: true,
				},
			],
			rest: [],
		};

		for (const kind of ["repair", "evaluate"] as const) {
			resetDocument();
			window.location.hash = "";
			const name = `eff-${kind}`;
			stubFetch(makeSnapshot([effort({ effort: name, kind })]), {
				[name]: journal,
			});
			if (!(await tryMountApp())) return;
			await vi.advanceTimersByTimeAsync(0);
			flushSync();

			const teasers = document.querySelectorAll("[data-journal-teaser]");
			expect(teasers.length).toBe(1);
			const teaser = teasers[0] as HTMLAnchorElement;
			expect(teaser.getAttribute("href")).toBe(`#/journal/${name}`);
			expect(teaser.textContent).toMatch(/2/);
			expect(teaser.textContent).toMatch(/open/i);

			teaser.click();
			flushSync();
			expect(window.location.hash).toBe(`#/journal/${name}`);
			// jsdom does not always emit hashchange when hash is assigned
			window.dispatchEvent(new HashChangeEvent("hashchange"));
			flushSync();
			expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
				"journal",
			);
		}
	});

	it("R4: deliver/incidental show no teaser", async () => {
		for (const kind of ["deliver", "incidental"] as const) {
			resetDocument();
			window.location.hash = "";
			stubFetch(makeSnapshot([effort({ effort: `eff-${kind}`, kind })]), {
				[`eff-${kind}`]: {
					open: [
						{
							id: "j1",
							record_type: "tuner:finding",
							subject: "x",
							open: true,
						},
					],
					rest: [],
				},
			});
			if (!(await tryMountApp())) return;
			await vi.advanceTimersByTimeAsync(0);
			flushSync();

			expect(document.querySelector("[data-journal-teaser]")).toBeNull();
			expect(document.querySelector("[data-side-journal-teaser]")).toBeNull();
		}
	});
});

describe("side-rail-journal-screen", () => {
	const sampleJournal = {
		open: [
			{
				id: "j-open",
				record_type: "tuner:finding",
				subject: "open-finding",
				text: "open body",
				open: true,
			},
		],
		rest: [
			{
				id: "j-earlier",
				record_type: "conductor:failed-attempt",
				subject: "earlier-attempt",
				text: "closed body",
				open: false,
			},
		],
	} as JournalResponse;

	it("R5: hash route opens journal screen loading GET /api/journal for effort", async () => {
		expect(journalHref("alpha")).toBe("#/journal/alpha");
		expect(parseRoute("#/journal/alpha")).toEqual({
			name: "journal",
			parts: ["journal", "alpha"],
			raw: "journal/alpha",
		});
		expect(appSource).toMatch(/journal\?effort=/);

		stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
			alpha: sampleJournal,
		});
		window.location.hash = journalHref("alpha");
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
			"journal",
		);
		expect(document.querySelector("[data-journal-screen]")).toBeTruthy();

		const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
		const journalCalls = fetchMock.mock.calls.filter((call) =>
			String(call[0]).includes("journal?effort="),
		);
		expect(journalCalls.length).toBeGreaterThan(0);
		expect(String(journalCalls[0]![0])).toMatch(/effort=alpha/);
	});

	it("R6: lists open then earlier; each row type + subject/text", async () => {
		const ordered = orderedJournal(sampleJournal);
		expect(ordered.map((r) => r.id)).toEqual(["j-open", "j-earlier"]);

		stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
			alpha: sampleJournal,
		});
		window.location.hash = journalHref("alpha");
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		const rows = [...document.querySelectorAll<HTMLElement>("[data-journal]")];
		expect(rows.map((r) => r.dataset.journal)).toEqual(["j-open", "j-earlier"]);
		expect(rows.map((r) => r.dataset.recordType)).toEqual([
			"tuner:finding",
			"conductor:failed-attempt",
		]);
		expect(rows[0]!.textContent).toMatch(/open-finding|open body/);
		expect(rows[1]!.textContent).toMatch(/earlier-attempt|closed body/);
	});

	it("R7: text filter by subject or text", async () => {
		const bySubject = filterJournal(orderedJournal(sampleJournal), "open-find");
		expect(bySubject.map((r) => r.id)).toEqual(["j-open"]);
		const byText = filterJournal(orderedJournal(sampleJournal), "closed body");
		expect(byText.map((r) => r.id)).toEqual(["j-earlier"]);

		stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
			alpha: sampleJournal,
		});
		window.location.hash = journalHref("alpha");
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		const input = document.querySelector<HTMLInputElement>(
			"[data-journal-filter]",
		);
		expect(input).toBeTruthy();
		input!.value = "earlier";
		input!.dispatchEvent(new Event("input", { bubbles: true }));
		flushSync();

		const rows = [...document.querySelectorAll<HTMLElement>("[data-journal]")];
		expect(rows.map((r) => r.dataset.journal)).toEqual(["j-earlier"]);
	});

	it("R8: activating row opens existing record detail overlay", async () => {
		expect(appSource).toMatch(/recordHref/);

		const recordPayload = {
			record: {
				id: "j-open",
				record_type: "tuner:finding",
				subject: "open-finding",
				body: "Record from journal row",
			},
		};

		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				if (url.includes("/api/token")) {
					return new Response(JSON.stringify({ token: "tok-1" }), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
				if (url.includes("/api/journal")) {
					return new Response(JSON.stringify(sampleJournal), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
				if (url.includes("/api/record")) {
					return new Response(JSON.stringify(recordPayload), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
				return new Response(
					JSON.stringify(
						makeSnapshot([effort({ effort: "alpha", kind: "repair" })]),
					),
					{
						status: 200,
						headers: { "content-type": "application/json" },
					},
				);
			}),
		);

		window.location.hash = journalHref("alpha");
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		const row = document.querySelector<HTMLElement>('[data-journal="j-open"]');
		expect(row).toBeTruthy();
		row!.click();
		flushSync();
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		expect(window.location.hash).toBe("#/record/j-open");
		expect(document.querySelector('[data-detail="record"]')).toBeTruthy();
	});

	it("R9: Esc or back returns to effort home", async () => {
		stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
			alpha: sampleJournal,
		});
		window.location.hash = journalHref("alpha");
		if (!(await tryMountApp())) return;
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
			"journal",
		);

		const back = document.querySelector<HTMLButtonElement>(
			'[data-act="close-journal"]',
		);
		expect(back).toBeTruthy();
		back!.click();
		flushSync();
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		flushSync();

		expect(window.location.hash).toBe("");
		expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
			"home",
		);
		expect(document.querySelector("[data-journal-screen]")).toBeNull();

		window.location.hash = journalHref("alpha");
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
			"journal",
		);

		window.dispatchEvent(
			new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
		);
		flushSync();
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		flushSync();

		expect(window.location.hash).toBe("");
		expect(document.querySelector<HTMLElement>("main")?.dataset.route).toBe(
			"home",
		);
	});
});
