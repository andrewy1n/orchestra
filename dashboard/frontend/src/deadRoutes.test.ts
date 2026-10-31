// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { detailTarget } from "./detail";
import { parseRoute } from "./router";
import type { DeepPartial, EffortView, Snapshot } from "./types";

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

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "",
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
		effort({ effort: "invoicing", goal: "Ship invoicing" }),
		effort({ effort: "web" }),
	],
} as Snapshot;

const needsPayload = {
	item: {
		kind: "needs-human",
		id: "n1",
		subject: "r3-unmet",
		text: "needs-human on send",
		body: "Check R3.",
		revision: "sha256:abc",
		approval: { confirm_choices: [] },
	},
};

const backlogPayload = {
	item: {
		id: "b1",
		subject: "park-idea",
		text: "Park the idea",
		status: "open",
		source: "",
	},
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

async function mountApp(hash: string) {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/needs?")) return json(needsPayload);
			if (url.includes("/api/backlog?")) return json(backlogPayload);
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("./App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

describe("retired needs route", () => {
	it("R5 the route #/needs renders the product home screen", async () => {
		await mountApp("#/needs");
		expect(document.querySelector("[data-product-index]")).not.toBeNull();
		expect(document.querySelector("main")?.getAttribute("data-route")).toBe(
			"home",
		);
	});

	it("R5 parseRoute returns home for #/needs", () => {
		expect(parseRoute("#/needs").name).toBe("home");
	});

	it("R5 the needs overlay deep link still resolves its target", () => {
		expect(detailTarget(parseRoute("#/needs/invoicing/n1"))).toEqual({
			kind: "needs",
			apiPath: "needs?effort=invoicing&id=n1",
		});
	});
});

describe("retired backlog route", () => {
	it("R6 the route #/backlog renders the product home screen", async () => {
		await mountApp("#/backlog");
		expect(document.querySelector("[data-product-index]")).not.toBeNull();
		expect(document.querySelector("main")?.getAttribute("data-route")).toBe(
			"home",
		);
	});

	it("R6 parseRoute returns home for #/backlog", () => {
		expect(parseRoute("#/backlog").name).toBe("home");
	});

	it("R6 the backlog overlay deep link still resolves its target", () => {
		expect(detailTarget(parseRoute("#/backlog/invoicing/b1"))).toEqual({
			kind: "backlog",
			apiPath: "backlog?effort=invoicing&id=b1",
		});
	});
});

describe("overlay deep links", () => {
	it.each([
		["R5", "needs", "n1", "r3-unmet"],
		["R6", "backlog", "b1", "park-idea"],
	])(
		"%s deep link #/%s/<effort>/<id> keeps the effort page and the overlay",
		async (_req, kind, id, who) => {
			await mountApp(`#/${kind}/invoicing/${id}`);
			expect(document.querySelector("main")?.getAttribute("data-route")).toBe(
				"effort",
			);
			expect(
				document.querySelector("main [data-effort-title]")?.textContent,
			).toBe("invoicing");
			const overlay = document.querySelector(`[data-detail="${kind}"]`);
			expect(overlay).not.toBeNull();
			expect(overlay?.textContent).toContain(who);
		},
	);
});
