// @vitest-environment node
import { describe, expect, it } from "vitest";

import { renderMarkdown } from "./markdown";

describe("renderMarkdown", () => {
	it("renders headings, paragraphs, bold, and code", () => {
		const html = renderMarkdown(
			"## Problem\n\nThe **store** is visible via `dashboard.model`.",
		);
		expect(html).toContain("<h4>Problem</h4>");
		expect(html).toContain("<strong>store</strong>");
		expect(html).toContain("<code>dashboard.model</code>");
		expect(html).toContain("<p>");
	});

	it("renders lists and fenced code", () => {
		const html = renderMarkdown("- one\n- two\n\n```\nconst x = 1\n```");
		expect(html).toContain("<ul>");
		expect(html).toContain("<li>one</li>");
		expect(html).toContain("<pre><code>const x = 1</code></pre>");
	});

	it("keeps wrapped lines on the same bullet and numbers ordered lists", () => {
		const bullets = renderMarkdown("- first line\n  continues here\n- second");
		expect(bullets).toContain("<li>first line continues here</li>");
		expect(bullets).toContain("<li>second</li>");
		const numbers = renderMarkdown("1. alpha\n   more\n2. beta");
		expect(numbers).toContain("<ol>");
		expect(numbers).toContain("<li>alpha more</li>");
		expect(numbers).toContain("<li>beta</li>");
	});

	it("escapes raw HTML", () => {
		const html = renderMarkdown("<script>alert(1)</script>");
		expect(html).not.toContain("<script>");
		expect(html).toContain("&lt;script&gt;");
	});
});
