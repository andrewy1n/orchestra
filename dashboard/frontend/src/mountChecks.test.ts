// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { type Component, flushSync, type mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mountApp } from "./testing/mountApp";

interface Recorded {
	status: number;
	body: unknown;
}

const ROUTES_TEST = resolve(
	process.cwd(),
	"../../tests/interfaces/test_http_routes.py",
);

function recordedBodies(): Record<string, Recorded> {
	const source = readFileSync(ROUTES_TEST, "utf8");
	const match = source.match(
		/EXPECTED: dict\[str, object\] = json\.loads\(\s*r"""([\s\S]*?)"""/,
	);
	if (!match) throw new Error("recorded HTTP bodies not found");
	return JSON.parse(match[1]) as Record<string, Recorded>;
}

const RECORDED = recordedBodies();

const TASK_ID = "<score:work-item:t-one>";
const RECORD_ID = "<tuner:finding:human-finding>";
const IDEA_ID = "<composer:idea:park-me>";

function recordedFor(url: URL): Recorded | undefined {
	const q = url.searchParams;
	switch (url.pathname) {
		case "/api/token":
			return RECORDED.token;
		case "/api/snapshot":
			return RECORDED.snapshot;
		case "/api/areas":
			return RECORDED.areas;
		case "/api/hub":
			return RECORDED.hub;
		case "/api/phase":
			return q.get("effort") === "alpha" && q.get("phase") === "p-one"
				? RECORDED.phase
				: undefined;
		case "/api/task":
			return q.get("id") === TASK_ID ? RECORDED.task : undefined;
		case "/api/journal":
			return q.get("effort") === "alpha" ? RECORDED.journal : undefined;
		case "/api/record":
			return q.get("id") === RECORD_ID ? RECORDED.record : undefined;
		case "/api/requirement":
			return q.get("effort") === "alpha" &&
				q.get("phase") === "p-one" &&
				q.get("id") === "R1"
				? RECORDED.requirement
				: undefined;
		case "/api/needs":
			return q.get("effort") === "alpha" && q.get("id") === RECORD_ID
				? RECORDED.needs
				: undefined;
		case "/api/backlog":
			return q.get("effort") === "alpha" && q.get("id") === IDEA_ID
				? RECORDED.backlog
				: undefined;
	}
	return undefined;
}

const enc = encodeURIComponent;

const SCREENS: ReadonlyArray<{ name: string; hash: string; text: string }> = [
	{ name: "Hub", hash: "", text: "Active phases" },
	{ name: "ProductIndex", hash: "#/areas", text: "Invoices." },
	{ name: "Area", hash: "#/area/billing", text: "No efforts in this area." },
	{ name: "Home", hash: "#/effort/alpha", text: "ship alpha" },
	{ name: "Journal", hash: "#/journal/alpha", text: "port-choice" },
	{ name: "PhasePage", hash: "#/phase/alpha/p-one", text: "first phase" },
	{
		name: "Overlay task",
		hash: `#/task/${enc(TASK_ID)}`,
		text: "placeholder text for Description.",
	},
	{
		name: "Overlay requirement",
		hash: "#/requirement/alpha/p-one/R1",
		text: "the route keeps its body",
	},
	{
		name: "Overlay record",
		hash: `#/record/${enc(RECORD_ID)}`,
		text: "tuner:finding",
	},
	{
		name: "Overlay needs",
		hash: `#/needs/alpha/${enc(RECORD_ID)}`,
		text: "Accept risk",
	},
	{
		name: "Overlay backlog",
		hash: `#/backlog/alpha/${enc(IDEA_ID)}`,
		text: "status: open",
	},
];

const FAILURE_SURFACES = [
	".error-note",
	".hub-status[role=alert]",
	".write-error",
	"[data-error]",
];

let mounted: ReturnType<typeof mount> | undefined;
let problems: string[] = [];
let unmatched: string[] = [];

function describeProblem(value: unknown): string {
	return value instanceof Error
		? (value.stack ?? value.message)
		: String(value);
}

function onWindowError(event: ErrorEvent) {
	problems.push(
		`window error: ${describeProblem(event.error ?? event.message)}`,
	);
	event.preventDefault();
}

function onRejection(event: PromiseRejectionEvent) {
	problems.push(`unhandled rejection: ${describeProblem(event.reason)}`);
	event.preventDefault();
}

beforeEach(() => {
	problems = [];
	unmatched = [];
	document.body.innerHTML = "";
	window.location.hash = "";
	vi.useFakeTimers();
	vi.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
		problems.push(`console.error: ${args.map(describeProblem).join(" ")}`);
	});
	vi.spyOn(console, "warn").mockImplementation((...args: unknown[]) => {
		problems.push(`console.warn: ${args.map(describeProblem).join(" ")}`);
	});
	window.addEventListener("error", onWindowError);
	window.addEventListener("unhandledrejection", onRejection);
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = new URL(String(input), "http://localhost");
			const hit = recordedFor(url);
			if (!hit) {
				unmatched.push(`${url.pathname}${url.search}`);
				return new Response(JSON.stringify({ error: "no recorded case" }), {
					status: 404,
				});
			}
			return new Response(JSON.stringify(hit.body), { status: hit.status });
		}),
	);
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	window.removeEventListener("error", onWindowError);
	window.removeEventListener("unhandledrejection", onRejection);
	document.body.innerHTML = "";
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

async function settle() {
	for (let i = 0; i < 4; i += 1) {
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
	}
}

describe("dashboard components mount against the recorded HTTP bodies", () => {
	it("serves the recorded bodies it mounts against", () => {
		for (const name of [
			"token",
			"snapshot",
			"areas",
			"hub",
			"phase",
			"task",
			"journal",
			"record",
			"requirement",
			"needs",
			"backlog",
		]) {
			expect(RECORDED[name]?.status, name).toBe(200);
		}
	});

	it.each(SCREENS)("$name mounts without an error", async ({ hash, text }) => {
		window.location.hash = hash;
		const module = await import("./App.svelte");
		mounted = (await mountApp(module.default as Component)).instance;
		await settle();

		expect(problems).toEqual([]);
		expect(unmatched).toEqual([]);
		for (const selector of FAILURE_SURFACES) {
			expect(
				[...document.querySelectorAll(selector)].map((el) => el.textContent),
				selector,
			).toEqual([]);
		}
		expect(document.body.textContent).toContain(text);
	});

	it("surfaces a failed answer instead of mounting silently", async () => {
		window.location.hash = "#/task/rec-missing";
		const module = await import("./App.svelte");
		mounted = (await mountApp(module.default as Component)).instance;
		await settle();
		expect(unmatched).toContain("/api/task?id=rec-missing");
		expect(document.querySelector(".error-note")).not.toBeNull();
	});
});
