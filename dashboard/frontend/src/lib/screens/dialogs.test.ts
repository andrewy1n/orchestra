// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { needsHref } from "../../detail";
import type { DeepPartial, EffortView, Snapshot } from "../../types";

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

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [
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
	],
} as Snapshot;

const needsPayload = {
	item: {
		kind: "blocking-question",
		id: "q1",
		subject: "which-backend",
		text: "which backend",
		revision: "sha256:abc",
		approval: {
			confirm_choices: [
				{ action: "approve", label: "Approve", note_required: false },
				{ action: "reject", label: "Reject", note_required: true },
			],
		},
	},
};

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function stubFetch() {
	const fetchMock = vi.fn(
		async (input: RequestInfo | URL, init?: RequestInit) => {
			const url = String(input);
			if ((init?.method || "GET").toUpperCase() === "POST") {
				return json({ ok: true });
			}
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/needs?")) return json(needsPayload);
			return json(snapshot);
		},
	);
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountApp() {
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

async function openDetail() {
	window.location.hash = needsHref("dashboard", "q1");
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await settle();
}

async function pressEscape() {
	const target = document.activeElement ?? document.body;
	target.dispatchEvent(
		new KeyboardEvent("keydown", {
			key: "Escape",
			bubbles: true,
			cancelable: true,
		}),
	);
	await settle();
}

function detail() {
	return document.querySelector<HTMLElement>('[data-detail="needs"]');
}

function confirm() {
	return document.querySelector<HTMLElement>("[data-confirm]");
}

function approveButton() {
	return document.querySelector<HTMLButtonElement>(
		'[data-write-action="approve"]',
	)!;
}

async function openConfirm() {
	const opener = approveButton();
	opener.focus();
	opener.click();
	await settle();
}

describe("detail and confirm dialogs", () => {
	beforeEach(async () => {
		stubFetch();
		await mountApp();
		await openDetail();
	});

	it("lays the detail dialog out as a column", () => {
		const content = detail();
		expect(content).toBeTruthy();
		expect(content!.classList.contains("flex-col")).toBe(true);
		expect(content!.classList.contains("flex")).toBe(true);
		expect(content!.classList.contains("grid")).toBe(false);
	});

	it("lets only the body of the detail dialog scroll", () => {
		const body = detail()!.querySelector<HTMLElement>(".overflow-y-auto");
		expect(body).toBeTruthy();
		expect(body!.classList.contains("min-h-0")).toBe(true);
		expect(body!.classList.contains("flex-1")).toBe(true);
	});

	it("closes the detail overlay on Escape", async () => {
		expect(detail()).toBeTruthy();
		await pressEscape();
		expect(detail()).toBeNull();
		expect(window.location.hash).not.toContain("/needs/");
	});

	it("closes only the confirm dialog on Escape over the detail overlay", async () => {
		await openConfirm();
		expect(confirm()).toBeTruthy();
		await pressEscape();
		expect(confirm()).toBeNull();
		expect(detail()).toBeTruthy();
	});

	it("closes the detail overlay on a second Escape", async () => {
		await openConfirm();
		await pressEscape();
		await pressEscape();
		expect(confirm()).toBeNull();
		expect(detail()).toBeNull();
	});

	it("keeps focus inside the detail dialog after the confirm dialog closes", async () => {
		await openConfirm();
		document.querySelector<HTMLButtonElement>("[data-confirm-cancel]")!.click();
		await settle();
		expect(confirm()).toBeNull();
		expect(detail()!.contains(document.activeElement)).toBe(true);
	});

	it("submits the confirm dialog on Enter in the note input", async () => {
		const fetchMock = vi.mocked(fetch);
		await openConfirm();
		const note = document.querySelector<HTMLInputElement>(
			"[data-confirm-note]",
		)!;
		note.focus();
		note.value = "looks good";
		note.dispatchEvent(new Event("input", { bubbles: true }));
		note.dispatchEvent(
			new KeyboardEvent("keydown", {
				key: "Enter",
				bubbles: true,
				cancelable: true,
			}),
		);
		await settle();
		const posts = fetchMock.mock.calls.filter(
			(call) =>
				((call[1] as RequestInit | undefined)?.method || "GET") === "POST",
		);
		expect(posts).toHaveLength(1);
		expect(String(posts[0]![0])).toContain("/api/needs");
		expect(
			JSON.parse(String((posts[0]![1] as RequestInit).body)),
		).toMatchObject({ id: "q1", action: "approve", note: "looks good" });
	});
});

describe("detail dialog opener focus", () => {
	it("returns focus to the opener after Escape closes the detail overlay", async () => {
		stubFetch();
		await mountApp();
		const row = document.querySelector<HTMLElement>('[data-needs="q1"]');
		expect(row).toBeTruthy();
		row!.focus();
		row!.click();
		await settle();
		expect(detail()).toBeTruthy();
		await pressEscape();
		expect(detail()).toBeNull();
		expect(document.activeElement).toBe(row);
	});
});
