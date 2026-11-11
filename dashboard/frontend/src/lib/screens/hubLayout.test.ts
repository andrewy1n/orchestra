// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { HubItem, HubResponse } from "../../api-types";
import type { Snapshot } from "../../types";

type Progress = NonNullable<HubItem["progress"]>;

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

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [],
} as unknown as Snapshot;

const progress: Progress = {
	weight: "full",
	stages: ["spec", "design", "tasks", "execute"].map((id, i) => ({
		id,
		state: i < 3 ? "done" : "current",
	})),
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
};

function item(overrides: Partial<HubItem>): HubItem {
	return {
		effort: "dashboard",
		href: "#/",
		kind: "phase",
		reason: "Updated recently",
		running: false,
		step: "",
		subject: "subject",
		title: "Title",
		updated_at: "2026-01-01T00:00:00Z",
		...overrides,
	};
}

const activePhases: HubItem[] = [
	item({
		href: "#/phase/dashboard/work-hub",
		subject: "work-hub",
		title: "Work hub",
		step: "execute",
		progress,
	}),
	item({
		effort: "workflow",
		href: "#/phase/workflow/skills-playbooks",
		subject: "skills-playbooks",
		title: "Skills playbooks",
		step: "verify",
		progress,
	}),
];

const workNext: HubItem[] = [
	item({
		href: "#/backlog/dashboard/dark-mode",
		kind: "idea",
		subject: "dark-mode",
		title: "Dark mode toggle",
		reason: "Updated 3 days ago",
	}),
];

const needsYou: HubItem[] = [
	item({
		href: "#/needs/dashboard/approve-spec",
		kind: "needs",
		subject: "approve-spec",
		title: "Approve the spec",
	}),
	item({
		effort: "workflow",
		href: "#/needs/workflow/sign-manual-check",
		kind: "needs",
		subject: "sign-manual-check",
		title: "Sign the manual check",
	}),
];

const openIdeas: HubItem[] = [
	item({
		href: "#/backlog/dashboard/dark-mode",
		kind: "idea",
		subject: "dark-mode",
		title: "Dark mode toggle",
	}),
	item({
		effort: "workflow",
		href: "#/backlog/workflow/retry-budget",
		kind: "idea",
		subject: "retry-budget",
		title: "Retry budget",
	}),
	item({
		href: "#/backlog/dashboard/export-csv",
		kind: "idea",
		subject: "export-csv",
		title: "Export to CSV",
	}),
];

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

async function mountHub(hub: Partial<HubResponse>) {
	const response: HubResponse = {
		active_phases: [],
		generated_at: "2026-01-01T00:00:00Z",
		needs_you: [],
		open_ideas: [],
		work_next: [],
		...hub,
	};
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/hub")) return json(response);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

const full = () => ({
	active_phases: activePhases,
	needs_you: needsYou,
	open_ideas: openIdeas,
	work_next: workNext,
});

function one(selector: string): HTMLElement {
	const found = document.querySelector<HTMLElement>(`[data-hub] ${selector}`);
	expect(found, selector).not.toBeNull();
	return found as HTMLElement;
}

function precedes(a: Element, b: Element): boolean {
	return Boolean(
		a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING,
	);
}

function links(root: Element): HTMLAnchorElement[] {
	return Array.from(root.querySelectorAll<HTMLAnchorElement>("a"));
}

describe("hub layout", () => {
	it("R1 the active phases section is the first section and precedes Work next", async () => {
		await mountHub(full());
		const sections = Array.from(
			document.querySelectorAll(
				"[data-hub] [data-active-phases], [data-hub] [data-hub-row], [data-hub] [data-panel]",
			),
		);
		expect(sections[0]).toBe(one("[data-active-phases]"));
		expect(precedes(one("[data-active-phases]"), one("[data-work-next]"))).toBe(
			true,
		);
		expect(document.querySelector('[data-panel="active-phases"]')).toBeNull();
	});

	it("R1 the active phases section holds one phase card per active phase", async () => {
		await mountHub(full());
		const cards = document.querySelectorAll(
			"[data-hub] [data-active-phases] [data-phase-card]",
		);
		expect(cards).toHaveLength(activePhases.length);
		expect(
			document.querySelectorAll("[data-hub] [data-phase-card]"),
		).toHaveLength(activePhases.length);
		const titles = Array.from(cards).map((card) =>
			card.querySelector("[data-title]")?.getAttribute("href"),
		);
		expect(titles).toEqual(activePhases.map((entry) => entry.href));
	});

	it("R14 Needs you and Work next sit in the same row container", async () => {
		await mountHub(full());
		const row = one("[data-hub-row]");
		expect(row.contains(one("[data-work-next]"))).toBe(true);
		expect(row.contains(one('[data-panel="needs-you"]'))).toBe(true);
		expect(row.contains(one('[data-panel="open-ideas"]'))).toBe(false);
	});

	it("R14 Open ideas comes after both Work next and Needs you", async () => {
		await mountHub(full());
		const ideas = one('[data-panel="open-ideas"]');
		expect(precedes(one("[data-work-next]"), ideas)).toBe(true);
		expect(precedes(one('[data-panel="needs-you"]'), ideas)).toBe(true);
		expect(precedes(one("[data-hub-row]"), ideas)).toBe(true);
	});

	it("R14 Needs you rows are unchanged", async () => {
		await mountHub(full());
		const found = links(one('[data-panel="needs-you"]'));
		expect(found.map((row) => row.getAttribute("href"))).toEqual(
			needsYou.map((entry) => entry.href),
		);
		found.forEach((row, i) => {
			expect(row.textContent).toContain((needsYou[i] as HubItem).title);
		});
	});

	it("R14 Open ideas rows are unchanged and grouped by effort", async () => {
		await mountHub(full());
		const panel = one('[data-panel="open-ideas"]');
		expect(links(panel)).toHaveLength(openIdeas.length);
		const text = panel.textContent ?? "";
		for (const idea of openIdeas) expect(text).toContain(idea.title);
		const order = (title: string) => text.indexOf(title);
		expect(order("Export to CSV")).toBeLessThan(order("Retry budget"));
		expect(order("Dark mode toggle")).toBeLessThan(order("Retry budget"));
		const labels = text.match(/dashboard|workflow/g) ?? [];
		expect(labels.filter((label) => label === "dashboard")).toHaveLength(1);
		expect(labels.filter((label) => label === "workflow")).toHaveLength(1);
	});

	it("R15 with no active phase there is no active phases section and no card", async () => {
		await mountHub({ ...full(), active_phases: [] });
		expect(document.querySelectorAll("[data-active-phases]")).toHaveLength(0);
		expect(document.querySelectorAll("[data-phase-card]")).toHaveLength(0);
		expect(
			document.querySelectorAll('[data-panel="active-phases"]'),
		).toHaveLength(0);
	});

	it("R15 with no active phase the other sections still render", async () => {
		await mountHub({ ...full(), active_phases: [] });
		const row = one("[data-hub-row]");
		expect(row.contains(one("[data-work-next]"))).toBe(true);
		expect(row.contains(one('[data-panel="needs-you"]'))).toBe(true);
		expect(one('[data-panel="open-ideas"]')).not.toBeNull();
	});
});
