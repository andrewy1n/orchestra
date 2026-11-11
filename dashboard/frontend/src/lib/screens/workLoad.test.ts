// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse, HubResponse } from "../../api-types";
import { type Snapshot, TOKEN_POLL_MS } from "../../types";

let mounted: ReturnType<typeof mount> | undefined;

const snapshot: Snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	store: "/test",
	efforts: [
		{
			effort: "alpha",
			goal: "Ship Alpha",
			kind: "deliver",
			area: "billing",
			finished: false,
			dormant: false,
			milestones: [],
			position: "",
			release_ready: false,
			phases: [
				{
					subject: "caps",
					title: "Caps",
					ordinal: 1,
					state: "in_progress",
					done: 0,
					total: 1,
					id: "p-caps",
					awaiting_signoff: false,
					elapsed_minutes: null,
					in_progress: [],
					milestone: "",
					milestone_title: "",
					release_ready: false,
					requirements: null,
					sitting: "",
					stage: "execute",
					suite: "",
					unset_estimates: 0,
					verified: null,
				},
			],
			tasks: [
				{
					id: "t-cap",
					subject: "cap",
					title: "Cap task",
					phase: "caps",
					status: "ready",
					assignee: "",
					attempts: 0,
					depends_on: [],
					estimate_minutes: null,
					executor: "inline",
					last_record_at: null,
					retry_budget: 0,
					running_since: null,
					size: "",
					waits_on: [],
					wave: null,
					write_root: "",
				},
			],
			needs_you: [],
			backlog: [],
		},
	],
};

const areas: AreasResponse = [
	{
		subject: "billing",
		title: "Billing",
		scope: "Invoices",
		open_count: 0,
		ideas: [],
	},
];

function work(title = "Review caps"): HubResponse {
	return {
		generated_at: "2026-01-01T00:00:00Z",
		work_next: [
			{
				kind: "phase",
				effort: "alpha",
				subject: "caps",
				title,
				reason: "Running now",
				running: true,
				href: "#/phase/alpha/caps",
				step: "execute",
				updated_at: "2026-01-01T00:00:00Z",
			},
		],
		active_phases: [],
		needs_you: [],
		open_ideas: [],
	};
}

function json(body: unknown, status = 200): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { "content-type": "application/json" },
	});
}

function deferred<T>(): {
	promise: Promise<T>;
	resolve: (value: T) => void;
} {
	let resolve: (value: T) => void = () => {
		throw new Error("Promise is not ready");
	};
	const promise = new Promise<T>((complete) => {
		resolve = complete;
	});
	return { promise, resolve };
}

async function settle(): Promise<void> {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountWork(): Promise<void> {
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

async function navigate(hash: string): Promise<void> {
	window.location.hash = hash;
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await settle();
}

function requests(fetcher: ReturnType<typeof vi.fn>): string[] {
	return fetcher.mock.calls.map(([input]) => String(input));
}

function stubRequests(
	snapshotResponse: () => Promise<Response> = async () => json(snapshot),
	tokenResponse: () => Promise<Response> = async () => json({ token: "tok-1" }),
): ReturnType<typeof vi.fn> {
	const fetcher = vi.fn(async (input: RequestInfo | URL) => {
		const url = String(input);
		if (url === "/api/snapshot") return snapshotResponse();
		if (url === "/api/token") return tokenResponse();
		if (url === "/api/hub") return json(work());
		if (url === "/api/areas") return json(areas);
		if (url.startsWith("/api/phase?")) {
			return json({
				tabs: ["overview", "spec", "tasks"],
				detail: {
					subject: "caps",
					effort: "alpha",
					title: "Caps",
					state: "in_progress",
					body: "Phase notes",
					tasks: [],
					evidence: { stage: "execute", weight: "light", requirements: [] },
				},
			});
		}
		if (url.startsWith("/api/task?")) {
			return json({
				detail: { id: "t-cap", subject: "cap", title: "Cap task" },
			});
		}
		if (url.startsWith("/api/journal?")) return json({ open: [], rest: [] });
		throw new Error(`Unexpected request: ${url}`);
	});
	vi.stubGlobal("fetch", fetcher);
	return fetcher;
}

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

describe("Work data loading", () => {
	it("R7 starts Work without requesting or awaiting the full snapshot", async () => {
		const pending = deferred<Response>();
		const fetcher = stubRequests(
			() => pending.promise,
			() => pending.promise,
		);
		await mountWork();
		expect(requests(fetcher)).toContain("/api/hub");
		expect(document.querySelector("[data-hub]")?.textContent).toContain(
			"Review caps",
		);
		expect(requests(fetcher)).not.toContain("/api/snapshot");
		expect(requests(fetcher)).not.toContain("/api/areas");
		expect(
			requests(fetcher).some((url) => url.startsWith("/api/journal")),
		).toBe(false);
	});

	it("R7 refreshes Work when the store token changes without loading a snapshot", async () => {
		let token = "tok-1";
		let title = "Review caps";
		const fetcher = vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url === "/api/hub") return json(work(title));
			if (url === "/api/token") return json({ token });
			if (url === "/api/areas") return json([]);
			return json({ ...snapshot, token });
		});
		vi.stubGlobal("fetch", fetcher);
		await mountWork();
		token = "tok-2";
		title = "Check the new work";
		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS);
		await settle();
		expect(document.querySelector("[data-hub]")?.textContent).toContain(title);
		expect(requests(fetcher)).not.toContain("/api/snapshot");
	});

	it("R7 does not accumulate token requests while a poll is pending", async () => {
		const pending = deferred<Response>();
		let tokenRequests = 0;
		const fetcher = stubRequests(undefined, async () => {
			tokenRequests += 1;
			return tokenRequests === 1 ? json({ token: "tok-1" }) : pending.promise;
		});
		await mountWork();
		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS * 5);
		await settle();
		expect(tokenRequests).toBe(2);
		expect(requests(fetcher)).not.toContain("/api/snapshot");
	});

	it("R7 keeps Work visible when token polling fails", async () => {
		stubRequests(undefined, async () => json({}, 503));
		await mountWork();
		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS);
		await settle();
		expect(document.querySelector("[data-hub]")?.textContent).toContain(
			"Review caps",
		);
		expect(document.querySelector("[data-status-text]")?.textContent).toContain(
			"GET /api/token failed: 503",
		);
	});

	it("R7 cancels a destination snapshot load after returning to Work", async () => {
		const pending = deferred<Response>();
		const fetcher = stubRequests(() => pending.promise);
		await mountWork();
		await navigate("#/effort/alpha");
		await navigate("#/");
		pending.resolve(json(snapshot));
		await settle();
		expect(document.querySelector("[data-hub]")?.textContent).toContain(
			"Review caps",
		);
		expect(
			requests(fetcher).some((url) => url.startsWith("/api/journal")),
		).toBe(false);
		expect(requests(fetcher)).not.toContain("/api/areas");
	});

	it("R7 returns to Work without refreshing full destination data", async () => {
		const fetcher = stubRequests();
		await mountWork();
		await navigate("#/effort/alpha");
		const completed = requests(fetcher).length;
		await navigate("#/");
		const fresh = requests(fetcher).slice(completed);
		expect(fresh).toContain("/api/hub");
		expect(fresh).not.toContain("/api/snapshot");
		expect(fresh).not.toContain("/api/areas");
		expect(fresh.some((url) => url.startsWith("/api/journal"))).toBe(false);
		expect(document.querySelector("[data-hub]")?.textContent).toContain(
			"Review caps",
		);
	});

	it("R9 loads Product data after leaving Work", async () => {
		const pending = deferred<Response>();
		const fetcher = stubRequests(() => pending.promise);
		await mountWork();
		await navigate("#/areas");
		expect(requests(fetcher)).toContain("/api/snapshot");
		pending.resolve(json(snapshot));
		await settle();
		expect(requests(fetcher)).toContain("/api/areas");
		expect(
			document.querySelector("[data-product-index]")?.textContent,
		).toContain("Billing");
		expect(
			document.querySelector("[data-product-index]")?.textContent,
		).toContain("1 effort");
	});

	it("R9 loads the effort snapshot when navigating from Work", async () => {
		const fetcher = stubRequests();
		await mountWork();
		await navigate("#/effort/alpha");
		expect(requests(fetcher)).toContain("/api/snapshot");
		expect(document.querySelector("[data-goal]")?.textContent).toBe(
			"Ship Alpha",
		);
	});

	it("R9 loads phase data when navigating from Work", async () => {
		const fetcher = stubRequests();
		await mountWork();
		await navigate("#/phase/alpha/caps");
		expect(requests(fetcher)).toContain("/api/snapshot");
		expect(requests(fetcher)).toContain("/api/phase?effort=alpha&phase=caps");
		expect(document.querySelector("[data-phase-page]")?.textContent).toContain(
			"Caps",
		);
	});

	it("R9 loads a task overlay and its phase context from Work", async () => {
		const fetcher = stubRequests();
		await mountWork();
		await navigate("#/task/t-cap");
		expect(requests(fetcher)).toContain("/api/snapshot");
		expect(requests(fetcher)).toContain("/api/task?id=t-cap");
		expect(
			document.querySelector('[data-detail="task"]')?.textContent,
		).toContain("Cap task");
		document
			.querySelector<HTMLButtonElement>('[data-act="close-detail"]')
			?.click();
		await settle();
		expect(window.location.hash).toBe("#/phase/alpha/caps");
	});

	it("R7 shows Work request errors without requiring a snapshot", async () => {
		const pending = deferred<Response>();
		const fetcher = stubRequests(() => pending.promise);
		fetcher.mockImplementation(async (input: RequestInfo | URL) => {
			if (String(input) === "/api/hub") return json({}, 503);
			if (String(input) === "/api/token") return json({ token: "tok-1" });
			return pending.promise;
		});
		await mountWork();
		expect(document.querySelector("[data-hub-status]")?.textContent).toContain(
			"GET /api/hub failed: 503",
		);
	});

	it("R9 keeps destination snapshot errors visible", async () => {
		stubRequests(async () => json({}, 503));
		await mountWork();
		await navigate("#/effort/alpha");
		expect(document.body.textContent).toContain(
			"GET /api/snapshot failed: 503",
		);
	});
});
