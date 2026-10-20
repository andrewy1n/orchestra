// @vitest-environment jsdom
import { afterEach, describe, expect, it } from "vitest";

import { closeDetail, openHash } from "./detail";

afterEach(() => {
  openHash("");
});

describe("overlay back", () => {
  it("returns to the previous screen instead of the dashboard", () => {
    openHash("#/phase/dashboard/p");
    openHash("#/requirement/dashboard/p/R1");
    expect(window.location.hash).toBe("#/requirement/dashboard/p/R1");

    closeDetail();
    expect(window.location.hash).toBe("#/phase/dashboard/p");

    closeDetail();
    expect(window.location.hash).toBe("");
  });

  it("returns to the dashboard when the overlay was opened directly", () => {
    openHash("");
    window.location.hash = "#/task/t1";
    closeDetail();
    expect(window.location.hash).toBe("");
  });

  it("treats a phase tab change as the same screen", () => {
    openHash("#/phase/dashboard/p");
    openHash("#/phase/dashboard/p/tab/design");
    closeDetail();
    expect(window.location.hash).toBe("");
  });
});
