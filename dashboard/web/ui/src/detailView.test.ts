// @vitest-environment node
import { describe, expect, it } from "vitest";

import { detailView } from "./detailView";

describe("detailView", () => {
  it("renders phase overview without dumping JSON", () => {
    const view = detailView(
      "phase",
      {
        detail: {
          subject: "web-dashboard",
          title: "Web dashboard",
          state: "in_progress",
          body: "Phase body marker",
          spec_body: "Spec marker",
        },
        tabs: ["overview", "spec"],
        decisions: { groups: [] },
      },
      "overview",
    );
    expect(view.who).toBe("Web dashboard");
    expect(view.sections[0]?.body).toContain("Phase body marker");
    expect(view.probe).toContain('"overview"');
    expect(view.probe).not.toMatch(/"detail"\s*:/);
  });

  it("switches phase tab to specification body", () => {
    const view = detailView(
      "phase",
      {
        detail: {
          title: "Web dashboard",
          body: "overview",
          spec_body: "Spec marker",
        },
        tabs: ["overview", "spec"],
      },
      "spec",
    );
    expect(view.sections[0]?.title).toBe("Specification");
    expect(view.sections[0]?.body).toContain("Spec marker");
  });
});
