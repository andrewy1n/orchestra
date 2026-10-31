import { describe, expect, it } from "vitest";
import { buildPhaseChrome } from "./phaseChrome";

function payload(state: string, statuses: string[], extra = {}) {
	return {
		detail: {
			state,
			tasks: statuses.map((status, index) => ({ id: `t${index}`, status })),
			...extra,
		},
	};
}

describe("phase Next line", () => {
	it("R7 derives the text from this phase when no next field is set", () => {
		const chrome = buildPhaseChrome(payload("in_progress", ["done", "ready"]));
		expect(chrome.nextAction).toBe("Continue ready work");
	});

	it("R7 prefers the payload next fields", () => {
		const chrome = buildPhaseChrome(
			payload("in_progress", ["ready"], { next_action: "Ship it" }),
		);
		expect(chrome.nextAction).toBe("Ship it");
	});

	it("R8 reads Phase complete for a done phase", () => {
		const chrome = buildPhaseChrome(payload("done", ["done", "done"]));
		expect(chrome.nextAction).toBe("Phase complete");
	});
});
