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
    expect(html).toContain("<pre>const x = 1</pre>");
  });

  it("escapes raw HTML", () => {
    const html = renderMarkdown('<script>alert(1)</script>');
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });
});
