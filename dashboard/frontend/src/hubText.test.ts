import { describe, expect, it } from "vitest";
import { firstSentence } from "./hubText";

describe("firstSentence", () => {
	it("keeps a short title as it is", () => {
		expect(firstSentence("Land through CI repair")).toBe(
			"Land through CI repair",
		);
	});

	it("returns the first sentence of a paragraph", () => {
		expect(
			firstSentence("Handle a stuck task. Inspect the worktree and resume."),
		).toBe("Handle a stuck task.");
	});

	it("cuts a long sentence at a word boundary with an ellipsis", () => {
		const out = firstSentence(`${"word ".repeat(40)}end.`, 50);
		expect(out.length).toBeLessThanOrEqual(51);
		expect(out.endsWith("…")).toBe(true);
		expect(out).not.toMatch(/\swor…$/);
	});

	it("does not split on a dot inside a name", () => {
		expect(firstSentence("Use orchestra.toml for the suite")).toBe(
			"Use orchestra.toml for the suite",
		);
	});
});
