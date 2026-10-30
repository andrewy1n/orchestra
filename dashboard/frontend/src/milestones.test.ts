/**
 * Milestone grouping helpers for the web dashboard Phases block.
 *
 * R3: Phases with no milestone appear in an Ungrouped group after all milestone groups.
 * R7: A milestone whose state is done starts collapsed (omitted from the initial expand set).
 * R8: The milestone that contains the currently selected phase (or the default phase when following) starts expanded.
 */

import { describe, expect, it } from "vitest";
import type { MilestoneRow } from "./api-types";
import {
	groupPhasesByMilestone,
	initialExpandedMilestones,
} from "./milestones";
import type { DeepPartial, EffortView, PhaseRow } from "./types";

function phase(
	partial: Partial<PhaseRow> & Pick<PhaseRow, "subject">,
): PhaseRow {
	return {
		title: partial.subject,
		ordinal: 0,
		state: "planned",
		done: 0,
		total: 0,
		...partial,
	} as PhaseRow;
}

function milestone(
	partial: Partial<MilestoneRow> & Pick<MilestoneRow, "subject">,
): MilestoneRow {
	return {
		title: partial.subject,
		ordinal: 0,
		state: "planned",
		done: 0,
		total: 0,
		...partial,
	} as MilestoneRow;
}

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		phases: [],
		tasks: [],
		needs_you: [],
		...partial,
	} as EffortView;
}

describe("groupPhasesByMilestone", () => {
	it("R3: places Ungrouped after milestone groups in snapshot order", () => {
		const view = effort({
			effort: "demo",
			milestones: [
				milestone({ subject: "cutover", title: "Cutover", ordinal: 1 }),
				milestone({ subject: "harden", title: "Harden", ordinal: 2 }),
			],
			phases: [
				phase({
					subject: "orphan",
					ordinal: 1,
					title: "Orphan phase",
				}),
				phase({
					subject: "p-cut",
					ordinal: 2,
					milestone: "cutover",
					milestone_title: "Cutover",
				}),
				phase({
					subject: "p-hard",
					ordinal: 3,
					milestone: "harden",
					milestone_title: "Harden",
				}),
			],
		});

		const groups = groupPhasesByMilestone(view);
		expect(groups.map((g) => g.key)).toEqual(["cutover", "harden", ""]);
		expect(groups.map((g) => g.title)).toEqual([
			"Cutover",
			"Harden",
			"Ungrouped",
		]);
		expect(groups[0]!.phases.map((p) => p.subject)).toEqual(["p-cut"]);
		expect(groups[1]!.phases.map((p) => p.subject)).toEqual(["p-hard"]);
		expect(groups[2]!.phases.map((p) => p.subject)).toEqual(["orphan"]);
		expect(groups[2]!.milestone).toBeNull();
	});

	it("R3: omits Ungrouped when every phase has a milestone", () => {
		const view = effort({
			effort: "demo",
			milestones: [milestone({ subject: "cutover", title: "Cutover" })],
			phases: [
				phase({
					subject: "p1",
					milestone: "cutover",
					milestone_title: "Cutover",
				}),
			],
		});
		const groups = groupPhasesByMilestone(view);
		expect(groups.map((g) => g.key)).toEqual(["cutover"]);
	});
});

describe("initialExpandedMilestones", () => {
	it("R7: omits done milestones from the initial expand set", () => {
		const view = effort({
			effort: "demo",
			milestones: [
				milestone({
					subject: "finished",
					title: "Finished",
					state: "done",
					done: 2,
					total: 2,
				}),
				milestone({
					subject: "live",
					title: "Live",
					state: "in_progress",
					done: 0,
					total: 1,
				}),
			],
			phases: [
				phase({
					subject: "old",
					state: "done",
					milestone: "finished",
					milestone_title: "Finished",
				}),
				phase({
					subject: "now",
					state: "in_progress",
					milestone: "live",
					milestone_title: "Live",
				}),
			],
		});

		const expanded = initialExpandedMilestones(view);
		expect(expanded.has("finished")).toBe(false);
		expect(expanded.has("live")).toBe(true);
	});

	it("R7: non-focus milestones stay collapsed even when not done", () => {
		const view = effort({
			effort: "demo",
			milestones: [
				milestone({ subject: "a", title: "A", state: "planned" }),
				milestone({ subject: "b", title: "B", state: "planned" }),
			],
			phases: [
				phase({ subject: "p-a", milestone: "a", milestone_title: "A" }),
				phase({
					subject: "p-b",
					state: "in_progress",
					milestone: "b",
					milestone_title: "B",
				}),
			],
		});

		const expanded = initialExpandedMilestones(view);
		expect(expanded.has("b")).toBe(true);
		expect(expanded.has("a")).toBe(false);
	});

	it("R8: expands the default-phase milestone", () => {
		const view = effort({
			effort: "demo",
			milestones: [
				milestone({ subject: "done-ms", title: "Done", state: "done" }),
				milestone({
					subject: "active-ms",
					title: "Active",
					state: "in_progress",
				}),
			],
			phases: [
				phase({
					subject: "past",
					state: "done",
					milestone: "done-ms",
					milestone_title: "Done",
				}),
				phase({
					subject: "current",
					state: "in_progress",
					milestone: "active-ms",
					milestone_title: "Active",
				}),
			],
		});

		const expanded = initialExpandedMilestones(view);
		expect(expanded.has("active-ms")).toBe(true);
		expect(expanded.has("done-ms")).toBe(false);
	});
});
