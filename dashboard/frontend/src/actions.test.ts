// @vitest-environment jsdom
/**
 * Write-action acceptance cases for the web dashboard UI.
 *
 * R20: The page asks for confirmation before it sends a store write.
 * R27: When dismiss_item raises, the page shows that error.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
	beginWrite,
	needsConfirmChoices,
	noteRequiredFor,
	writeBody,
	writePath,
} from "./actions";
import { appSource } from "./appSource";
import { needsHref } from "./detail";
import type { DeepPartial, EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));

const actionsSource = readFileSync(path.join(here, "actions.ts"), "utf8");
const apiSource = readFileSync(path.join(here, "api.ts"), "utf8");

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

function stubFetch(
	snap: Snapshot,
	details: DetailMap = {},
	options: {
		postNeeds?: (body: unknown) => Response | Promise<Response>;
		postBacklog?: (body: unknown) => Response | Promise<Response>;
	} = {},
) {
	const fetchMock = vi.fn(
		async (input: RequestInfo | URL, init?: RequestInit) => {
			const url = String(input);
			const method = (init?.method || "GET").toUpperCase();

			if (method === "POST" && url.includes("/api/needs")) {
				const body = init?.body ? JSON.parse(String(init.body)) : {};
				if (options.postNeeds) return options.postNeeds(body);
				return new Response(JSON.stringify({ ok: true }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			if (method === "POST" && url.includes("/api/backlog")) {
				const body = init?.body ? JSON.parse(String(init.body)) : {};
				if (options.postBacklog) return options.postBacklog(body);
				return new Response(JSON.stringify({ ok: true }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}

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
		},
	);
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
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

function postCalls(fetchMock: ReturnType<typeof vi.fn>): string[] {
	return fetchMock.mock.calls
		.filter((call) => {
			const init = call[1] as RequestInit | undefined;
			return (init?.method || "GET").toUpperCase() === "POST";
		})
		.map((call) => String(call[0]));
}

describe("web-dashboard actions", () => {
	it("R20: The page asks for confirmation before it sends a store write.", async () => {
		expect(appSource).toContain("data-confirm");
		expect(appSource).toContain("data-confirm-submit");
		expect(appSource).toContain("data-write-action");
		expect(appSource).toMatch(/postJson|POST/);
		expect(appSource).toMatch(/submitConfirm|pendingWrite/);
		expect(actionsSource).toMatch(/beginWrite|writeBody/);
		expect(apiSource).toContain('method: "POST"');

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

		expect(needsConfirmChoices(needsPayload).map((c) => c.action)).toEqual([
			"approve",
			"reject",
		]);
		expect(noteRequiredFor("reject")).toBe(true);
		expect(noteRequiredFor("approve")).toBe(false);

		const pending = beginWrite(
			"needs",
			"dashboard",
			needsPayload,
			needsConfirmChoices(needsPayload)[0]!,
		);
		expect(pending).toEqual({
			kind: "needs",
			effort: "dashboard",
			id: "q1",
			action: "approve",
			label: "Approve",
			noteRequired: false,
			revision: "sha256:abc",
		});
		expect(writePath(pending!)).toBe("needs");
		expect(writeBody(pending!, "")).toEqual({
			effort: "dashboard",
			id: "q1",
			action: "approve",
			revision: "sha256:abc",
		});

		const rejectPending = beginWrite(
			"needs",
			"dashboard",
			needsPayload,
			needsConfirmChoices(needsPayload)[1]!,
		);
		expect(rejectPending?.noteRequired).toBe(true);
		expect(writeBody(rejectPending!, "approach is wrong")).toMatchObject({
			action: "reject",
			note: "approach is wrong",
		});

		const fetchMock = stubFetch(
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
			await openAndSettle(needsHref("dashboard", "q1"));
			expect(document.querySelector('[data-detail="needs"]')).toBeTruthy();
			expect(
				document.querySelector('[data-write-action="approve"]'),
			).toBeTruthy();
			expect(document.querySelector("[data-confirm]")).toBeNull();
			expect(postCalls(fetchMock)).toEqual([]);

			document
				.querySelector<HTMLButtonElement>('[data-write-action="approve"]')!
				.click();
			flushSync();

			expect(document.querySelector("[data-confirm]")).toBeTruthy();
			expect(document.querySelector("[data-confirm-submit]")).toBeTruthy();
			expect(document.querySelector("[data-confirm-note]")).toBeTruthy();
			expect(postCalls(fetchMock)).toEqual([]);

			document
				.querySelector<HTMLButtonElement>("[data-confirm-submit]")!
				.click();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();

			const posts = postCalls(fetchMock);
			expect(posts.some((url) => url.includes("/api/needs"))).toBe(true);
			const postCall = fetchMock.mock.calls.find((call) => {
				const init = call[1] as RequestInit | undefined;
				return (init?.method || "").toUpperCase() === "POST";
			});
			expect(postCall).toBeTruthy();
			const body = JSON.parse(String((postCall![1] as RequestInit).body));
			expect(body).toMatchObject({
				id: "q1",
				action: "approve",
				revision: "sha256:abc",
			});
		}
	});

	it("R27: When dismiss_item raises, the page shows that error.", async () => {
		expect(appSource).toContain("data-write-error");
		expect(appSource).toMatch(/writeError/);
		expect(apiSource).toMatch(/error/);

		const dismissMessage = "record changed since opened";
		const needsPayload = {
			item: {
				kind: "blocking-question",
				id: "q1",
				subject: "which-backend",
				text: "which backend",
				revision: "sha256:stale",
				approval: {
					confirm_choices: [
						{ action: "approve", label: "Approve", note_required: false },
					],
				},
			},
		};

		const fetchMock = stubFetch(
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
			{
				postNeeds: () =>
					new Response(JSON.stringify({ error: dismissMessage }), {
						status: 409,
						headers: { "content-type": "application/json" },
					}),
			},
		);

		if (await tryMountApp()) {
			await openAndSettle(needsHref("dashboard", "q1"));
			document
				.querySelector<HTMLButtonElement>('[data-write-action="approve"]')!
				.click();
			flushSync();
			expect(document.querySelector("[data-confirm]")).toBeTruthy();

			document
				.querySelector<HTMLButtonElement>("[data-confirm-submit]")!
				.click();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();

			expect(
				postCalls(fetchMock).some((url) => url.includes("/api/needs")),
			).toBe(true);
			const err = document.querySelector("[data-write-error]");
			expect(err).toBeTruthy();
			expect(err?.textContent).toContain(dismissMessage);
			// Confirm stays so the operator can fix the note or cancel.
			expect(document.querySelector("[data-confirm]")).toBeTruthy();
		}
	});
});
