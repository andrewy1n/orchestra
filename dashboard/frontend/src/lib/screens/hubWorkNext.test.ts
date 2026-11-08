// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { HubItem, HubResponse } from "../../api-types";
import { parseRoute } from "../../router";
import type { Snapshot } from "../../types";

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

const workNext: HubItem[] = [
	{
		effort: "dashboard",
		href: "#/phase/dashboard/work-hub",
		kind: "phase",
		reason: "Running now",
		running: true,
		step: "execute",
		subject: "work-hub",
		title: "Work hub",
		updated_at: "2026-01-01T00:00:00Z",
	},
	{
		effort: "dashboard",
		href: "#/needs/dashboard/approve-spec",
		kind: "needs",
		reason: "Updated 2 hours ago",
		running: false,
		step: "",
		subject: "approve-spec",
		title: "Approve the spec",
		updated_at: "2025-12-31T22:00:00Z",
	},
	{
		effort: "dashboard",
		href: "#/backlog/dashboard/dark-mode",
		kind: "idea",
		reason: "Updated 3 days ago",
		running: false,
		step: "",
		subject: "dark-mode",
		title: "Dark mode toggle",
		updated_at: "2025-12-29T00:00:00Z",
	},
];

const hubResponse: HubResponse = {
	active_phases: [],
	generated_at: "2026-01-01T00:00:00Z",
	needs_you: [],
	open_ideas: [],
	work_next: workNext,
};

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

async function mountHub() {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/hub")) return json(hubResponse);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function rows(): HTMLAnchorElement[] {
	return Array.from(
		document.querySelectorAll<HTMLAnchorElement>(
			"[data-hub] [data-work-next] a",
		),
	);
}

function resolves(href: string): boolean {
	const route = parseRoute(href);
	if (route.name === "phase") return route.parts.length >= 3;
	const first = route.parts[0];
	return route.name === "effort" && (first === "needs" || first === "backlog");
}

describe("hub work next", () => {
	it("R8 every ranked row shows a non-empty reason line", async () => {
		await mountHub();
		const found = rows();
		expect(found).toHaveLength(workNext.length);
		found.forEach((row, i) => {
			const reason = row.querySelector("[data-reason]")?.textContent?.trim();
			expect(reason).toBe(workNext[i]?.reason);
		});
	});

	it("R8 the running phase shows its step and a Running now reason", async () => {
		await mountHub();
		const first = rows()[0];
		expect(first?.textContent).toContain("Work hub");
		expect(first?.textContent).toContain("execute");
		expect(first?.querySelector("[data-reason]")?.textContent).toContain(
			"Running now",
		);
	});

	it("R9 each row link href equals the item href", async () => {
		await mountHub();
		const hrefs = rows().map((row) => row.getAttribute("href"));
		expect(hrefs).toEqual(workNext.map((item) => item.href));
	});

	it("R9 every row href resolves to a phase, needs or backlog route", async () => {
		await mountHub();
		const found = rows();
		expect(found.length).toBeGreaterThan(0);
		for (const row of found) {
			expect(resolves(row.getAttribute("href") ?? "")).toBe(true);
		}
	});
});
