// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { HubItem, HubResponse } from "../../api-types";
import type { Snapshot } from "../../types";

let mounted: ReturnType<typeof mount> | undefined;
let fetchMock: ReturnType<typeof vi.fn>;

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

const progress: NonNullable<HubItem["progress"]> = {
	weight: "full",
	stages: [{ id: "execute", state: "current" }],
	tasks: {
		done: 1,
		running: 1,
		remaining: 1,
		total: 3,
		wave: 1,
		label: "1 of 3",
	},
	requirements: { proven: 1, total: 2, label: "1 of 2 proven" },
	repairs: null,
	blockers: { shown: [], more: 0, text: "Nothing blocks close" },
};

const activePhases: HubItem[] = [
	item({
		effort: "dashboard",
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

const needsYou: HubItem[] = [
	item({
		effort: "dashboard",
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
		effort: "dashboard",
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
		effort: "dashboard",
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
	fetchMock = vi.fn(async (input: RequestInfo | URL) => {
		const url = String(input);
		if (url.includes("/api/token")) return json({ token: snapshot.token });
		if (url.includes("/api/areas")) return json([]);
		if (url.includes("/api/hub")) return json(response);
		if (url.includes("/api/journal")) return json({ open: [], rest: [] });
		return json(snapshot);
	});
	vi.stubGlobal("fetch", fetchMock);
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function panel(name: string): HTMLElement | null {
	return document.querySelector<HTMLElement>(
		`[data-hub] [data-panel="${name}"]`,
	);
}

function links(name: string): HTMLAnchorElement[] {
	return Array.from(
		panel(name)?.querySelectorAll<HTMLAnchorElement>("a") ?? [],
	);
}

describe("hub panels", () => {
	it("R2 active phases cards show effort, phase title and link", async () => {
		await mountHub({ active_phases: activePhases });
		const cards = Array.from(
			document.querySelectorAll<HTMLElement>(
				"[data-hub] [data-active-phases] [data-phase-card]",
			),
		);
		expect(cards).toHaveLength(activePhases.length);
		cards.forEach((card, i) => {
			const expected = activePhases[i] as HubItem;
			expect(card.querySelector("[data-title]")?.getAttribute("href")).toBe(
				expected.href,
			);
			expect(card.textContent).toContain(expected.effort);
			expect(card.textContent).toContain(expected.title);
		});
	});

	it("R3 needs you panel shows the open items from needs_you", async () => {
		await mountHub({ needs_you: needsYou });
		const found = links("needs-you");
		expect(found.map((row) => row.getAttribute("href"))).toEqual(
			needsYou.map((entry) => entry.href),
		);
		found.forEach((row, i) => {
			expect(row.textContent).toContain((needsYou[i] as HubItem).title);
		});
	});

	it("R4 open ideas panel shows open_ideas grouped by effort", async () => {
		await mountHub({ open_ideas: openIdeas });
		const found = links("open-ideas");
		expect(found).toHaveLength(openIdeas.length);
		const text = panel("open-ideas")?.textContent ?? "";
		for (const idea of openIdeas) expect(text).toContain(idea.title);
		const order = (title: string) => text.indexOf(title);
		expect(order("Export to CSV")).toBeLessThan(order("Retry budget"));
		expect(order("Dark mode toggle")).toBeLessThan(order("Retry budget"));
		const labels = text.match(/dashboard|workflow/g) ?? [];
		expect(labels.filter((label) => label === "dashboard")).toHaveLength(1);
		expect(labels.filter((label) => label === "workflow")).toHaveLength(1);
	});

	it("R10 with all four lists empty one empty-state note shows and no panels render", async () => {
		await mountHub({});
		expect(
			document.querySelectorAll("[data-hub] [data-hub-empty]"),
		).toHaveLength(1);
		expect(
			document.querySelector("[data-hub-empty]")?.textContent?.trim(),
		).not.toBe("");
		expect(document.querySelectorAll("[data-panel]")).toHaveLength(0);
	});

	it("R11 the mounted hub has no button, form or input and fires no non-GET request", async () => {
		await mountHub({
			active_phases: activePhases,
			needs_you: needsYou,
			open_ideas: openIdeas,
		});
		expect(panel("needs-you")).not.toBeNull();
		const hub = document.querySelector("[data-hub]");
		expect(hub).not.toBeNull();
		expect(hub?.querySelectorAll("button, form, input")).toHaveLength(0);
		const methods = fetchMock.mock.calls.map((call) =>
			String(
				(call[1] as RequestInit | undefined)?.method ?? "GET",
			).toUpperCase(),
		);
		expect(methods.length).toBeGreaterThan(0);
		expect(methods.every((method) => method === "GET")).toBe(true);
	});
});
