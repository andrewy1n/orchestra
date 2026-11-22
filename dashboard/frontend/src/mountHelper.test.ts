// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Faulty from "./testing/fixtures/Faulty.svelte";
import { mountApp } from "./testing/mountApp";

beforeEach(() => {
	document.body.innerHTML = "";
});

afterEach(() => {
	document.body.innerHTML = "";
	vi.restoreAllMocks();
});

describe("mountApp", () => {
	it("mounts a healthy component and returns a handle", async () => {
		const handle = await mountApp(Faulty, { props: { mode: "ok" } });
		expect(handle).toBeTruthy();
		expect(document.querySelector("[data-fixture]")?.textContent).toBe("ok");
		handle.unmount();
	});

	it("rethrows when the component mount throws", async () => {
		await expect(
			mountApp(Faulty, { props: { mode: "throw" } }),
		).rejects.toThrow("fixture mount failure");
	});

	it("fails on console.error during mount", async () => {
		vi.spyOn(console, "error").mockImplementation(() => {});
		await expect(
			mountApp(Faulty, { props: { mode: "console-error" } }),
		).rejects.toThrow("fixture console error");
	});

	it("fails on an unhandled rejection during mount", async () => {
		await expect(
			mountApp(Faulty, { props: { mode: "reject" } }),
		).rejects.toThrow("fixture rejection");
	});

	it("fails on an error event during mount", async () => {
		await expect(
			mountApp(Faulty, { props: { mode: "error-event" } }),
		).rejects.toThrow("fixture error event");
	});

	it("never signals failure with a falsy return value", async () => {
		for (const mode of ["throw", "console-error", "reject", "error-event"]) {
			vi.spyOn(console, "error").mockImplementation(() => {});
			const outcome = await mountApp(Faulty, {
				props: { mode: mode as "throw" },
			}).then(
				(value) => ({ returned: value }),
				() => ({ threw: true }),
			);
			expect(outcome, mode).toEqual({ threw: true });
		}
	});
});
