// @vitest-environment node
import { describe, expect, it } from "vitest";

import { renderMarkdown } from "./markdown";

const REQUIREMENTS =
	"## Requirements\n\nR1: first requirement\nR2: second requirement\nR10: tenth requirement";

function items(html: string): string[] {
	return [...html.matchAll(/<li>(.*?)<\/li>/g)].map((match) => match[1] ?? "");
}

describe("phase notes", () => {
	it("R11 each Rn line of a Requirements section renders as its own block", () => {
		const html = renderMarkdown(REQUIREMENTS);
		expect(items(html)).toEqual([
			"R1: first requirement",
			"R2: second requirement",
			"R10: tenth requirement",
		]);
		expect(html).not.toContain("<p>R1");
	});

	it("R11 a wrapped Rn line stays in its block and the next Rn line starts a new one", () => {
		const html = renderMarkdown("R1: first\n  continues here\nR2: second");
		expect(items(html)).toEqual(["R1: first continues here", "R2: second"]);
	});

	it("R11 prose lines that do not start with Rn stay in one paragraph", () => {
		const html = renderMarkdown("Intro line\nsecond line\n\nR1: only");
		expect(html).toContain("<p>Intro line second line</p>");
		expect(items(html)).toEqual(["R1: only"]);
		expect(renderMarkdown("Rx: not a requirement")).toBe(
			"<p>Rx: not a requirement</p>",
		);
	});
});
