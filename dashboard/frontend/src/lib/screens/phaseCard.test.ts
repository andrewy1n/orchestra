// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { HubItem } from "../../api-types";

type Progress = NonNullable<HubItem["progress"]>;

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	document.body.innerHTML = "";
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	document.body.innerHTML = "";
});

const FULL_STAGES = [
	"spec",
	"design",
	"tasks",
	"execute",
	"verify",
	"review",
	"land",
	"close",
];

function stages(states: string[], ids: string[] = FULL_STAGES) {
	return ids.map((id, i) => ({ id, state: states[i] ?? "pending" }));
}

function progress(over: Partial<Progress> = {}): Progress {
	return {
		weight: "full",
		stages: stages(["done", "done", "done", "current"]),
		tasks: {
			done: 3,
			running: 1,
			remaining: 2,
			total: 6,
			wave: 2,
			label: "3 of 6 · wave 2",
		},
		requirements: { proven: 3, total: 5, label: "3 of 5 proven" },
		repairs: null,
		blockers: { shown: [], more: 0, text: "Nothing blocks close" },
		...over,
	};
}

function item(over: Partial<HubItem> = {}, p: Partial<Progress> = {}): HubItem {
	return {
		effort: "dashboard",
		href: "#/phase/dashboard/phase-progress-cards",
		kind: "phase",
		reason: "Updated 2 days ago",
		running: false,
		step: "execute",
		subject: "phase-progress-cards",
		title: "Phase progress cards",
		updated_at: "2026-01-01T00:00:00Z",
		progress: progress(p),
		...over,
	} as HubItem;
}

async function render(it: HubItem): Promise<HTMLElement> {
	const module = await import("./PhaseCard.svelte");
	mounted = mount(module.default as Component<{ item: HubItem }>, {
		target: document.body,
		props: { item: it },
	});
	flushSync();
	const card = document.querySelector<HTMLElement>("[data-phase-card]");
	if (!card) throw new Error("no [data-phase-card] rendered");
	return card;
}

function text(el: Element | null | undefined): string {
	return (el?.textContent ?? "").replace(/\s+/g, " ").trim();
}

describe("phase card header", () => {
	it("R4 header shows title, effort, weight and the time since last write", async () => {
		const card = await render(item());
		const header = card.querySelector("[data-card-header]");
		expect(text(header)).toContain("Phase progress cards");
		expect(text(header?.querySelector("[data-effort]"))).toBe("dashboard");
		expect(text(header?.querySelector("[data-weight]"))).toBe("full");
		expect(text(header?.querySelector("[data-reason]"))).toContain(
			"2 days ago",
		);
	});

	it("R4 a running phase shows running with the time", async () => {
		const card = await render(
			item({ running: true, reason: "Updated 4 min ago" }),
		);
		const running = card.querySelector("[data-running]");
		expect(running).not.toBeNull();
		expect(text(running)).toContain("running");
		expect(text(card.querySelector("[data-reason]"))).toContain("4 min ago");
	});

	it("R4 a phase that is not running shows no running marker", async () => {
		const card = await render(item());
		expect(card.querySelector("[data-running]")).toBeNull();
	});

	it("R4 the title links to the phase page", async () => {
		const it = item();
		const card = await render(it);
		const link = card.querySelector<HTMLAnchorElement>(
			"[data-card-header] a[data-title]",
		);
		expect(link?.getAttribute("href")).toBe(it.href);
		expect(text(link)).toBe("Phase progress cards");
	});
});

describe("phase card stepper", () => {
	it("R5 stepper shows the eight stages in order with state marks", async () => {
		const card = await render(item());
		const segs = Array.from(card.querySelectorAll<HTMLElement>("[data-stage]"));
		expect(segs.map((s) => s.getAttribute("data-stage"))).toEqual(FULL_STAGES);
		expect(segs.map((s) => text(s))).toEqual(FULL_STAGES);
		expect(segs.map((s) => s.getAttribute("data-state"))).toEqual([
			"done",
			"done",
			"done",
			"current",
			"pending",
			"pending",
			"pending",
			"pending",
		]);
	});

	it("R5 the current stage is marked aria-current", async () => {
		const card = await render(item());
		const current = card.querySelectorAll('[data-stage][aria-current="step"]');
		expect(current).toHaveLength(1);
		expect(current[0]?.getAttribute("data-stage")).toBe("execute");
	});

	it("R5 a light phase renders the six stages it receives", async () => {
		const light = ["spec", "tasks", "execute", "verify", "land", "close"];
		const card = await render(
			item({}, { weight: "light", stages: stages(["done", "done"], light) }),
		);
		const segs = Array.from(card.querySelectorAll<HTMLElement>("[data-stage]"));
		expect(segs.map((s) => s.getAttribute("data-stage"))).toEqual(light);
		expect(segs.map((s) => s.getAttribute("data-state"))).toEqual([
			"done",
			"done",
			"pending",
			"pending",
			"pending",
			"pending",
		]);
	});
});

describe("phase card tasks", () => {
	it("R8 task bar shows done, running and remaining segments with the label", async () => {
		const card = await render(item());
		const row = card.querySelector("[data-tasks]");
		const seg = (k: string) =>
			Array.from(row?.querySelectorAll(`[data-segment="${k}"]`) ?? []);
		expect(seg("done")).toHaveLength(3);
		expect(seg("running")).toHaveLength(1);
		expect(seg("remaining")).toHaveLength(2);
		expect(text(row?.querySelector("[data-label]"))).toBe("3 of 6 · wave 2");
	});

	it("R9 no tasks shows no tasks yet and no bar", async () => {
		const card = await render(
			item(
				{},
				{
					tasks: {
						done: 0,
						running: 0,
						remaining: 0,
						total: 0,
						wave: null,
						label: "no tasks yet",
					},
				},
			),
		);
		const row = card.querySelector("[data-tasks]");
		expect(text(row)).toContain("no tasks yet");
		expect(row?.querySelector("[data-segment]")).toBeNull();
		expect(row?.querySelector("[data-bar]")).toBeNull();
	});
});

describe("phase card requirements", () => {
	it("R10 requirements row shows the proven label and a bar", async () => {
		const card = await render(item());
		const row = card.querySelector("[data-requirements]");
		expect(text(row)).toContain("3 of 5 proven");
		expect(row?.querySelector("[data-bar]")).not.toBeNull();
	});

	it("R10 no requirements shows no requirements and no bar", async () => {
		const card = await render(
			item(
				{},
				{
					requirements: { proven: 0, total: 0, label: "no requirements" },
				},
			),
		);
		const row = card.querySelector("[data-requirements]");
		expect(text(row)).toContain("no requirements");
		expect(row?.querySelector("[data-bar]")).toBeNull();
	});
});

describe("phase card repairs", () => {
	it("R11 repairs row is absent when repairs is null", async () => {
		const card = await render(item());
		expect(card.querySelector("[data-repairs]")).toBeNull();
	});

	it("R11 repairs row shows the label when repairs is present", async () => {
		const card = await render(
			item({}, { repairs: { used: 2, limit: 3, label: "2 of 3 fix tasks" } }),
		);
		const row = card.querySelector("[data-repairs]");
		expect(row).not.toBeNull();
		expect(text(row)).toContain("Repairs");
		expect(text(row)).toContain("2 of 3 fix tasks");
	});
});

describe("phase card gate line", () => {
	it("R12 lists the shown blockers and the more count", async () => {
		const card = await render(
			item(
				{},
				{
					blockers: {
						shown: ["Review pending", "Task t1 failed"],
						more: 3,
						text: "Blocks close: Review pending; Task t1 failed; +3 more",
					},
				},
			),
		);
		const gate = card.querySelector("[data-gate]");
		const shown = Array.from(gate?.querySelectorAll("[data-blocker]") ?? []);
		expect(shown.map((b) => text(b))).toEqual([
			"Review pending",
			"Task t1 failed",
		]);
		expect(text(gate)).toContain("Blocks close");
		expect(text(gate?.querySelector("[data-more]"))).toBe("+3 more");
	});

	it("R12 no more count is shown when nothing is hidden", async () => {
		const card = await render(
			item(
				{},
				{
					blockers: {
						shown: ["Review pending"],
						more: 0,
						text: "Blocks close: Review pending",
					},
				},
			),
		);
		expect(card.querySelector("[data-gate] [data-more]")).toBeNull();
	});

	it("R12 says Nothing blocks close when there are no blockers", async () => {
		const card = await render(item());
		const gate = card.querySelector("[data-gate]");
		expect(text(gate)).toContain("Nothing blocks close");
		expect(gate?.querySelector("[data-blocker]")).toBeNull();
	});
});
