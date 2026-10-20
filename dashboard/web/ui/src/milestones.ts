import { defaultPhase } from "./efforts";
import type { EffortView, MilestoneRow, PhaseRow } from "./types";

/** One milestone (or Ungrouped) bucket of phases for the Phases block. */
export interface MilestoneGroup {
  /** Milestone subject, or `""` for Ungrouped. */
  key: string;
  title: string;
  milestone: MilestoneRow | null;
  phases: PhaseRow[];
}

/**
 * Group phases under snapshot milestones (order preserved), then Ungrouped.
 * Phases with no `milestone` land in Ungrouped when that bucket is non-empty.
 */
export function groupPhasesByMilestone(effort: EffortView): MilestoneGroup[] {
  const milestones = effort.milestones ?? [];
  const byKey = new Map<string, PhaseRow[]>();
  for (const phase of effort.phases) {
    const key = phase.milestone || "";
    const list = byKey.get(key);
    if (list) list.push(phase);
    else byKey.set(key, [phase]);
  }
  const groups: MilestoneGroup[] = milestones.map((milestone) => ({
    key: milestone.subject,
    title: milestone.title || milestone.subject,
    milestone,
    phases: byKey.get(milestone.subject) ?? [],
  }));
  const ungrouped = byKey.get("") ?? [];
  if (ungrouped.length > 0) {
    groups.push({
      key: "",
      title: "Ungrouped",
      milestone: null,
      phases: ungrouped,
    });
  }
  return groups;
}

/**
 * Milestone subjects that should start expanded.
 * Done milestones are omitted unless they contain the focus phase;
 * the milestone of the selected phase (or default when `phaseSubject` is null)
 * is always included when present.
 */
export function initialExpandedMilestones(
  effort: EffortView,
  phaseSubject: string | null,
): Set<string> {
  const focus = phaseSubject ?? defaultPhase(effort);
  const expanded = new Set<string>();
  for (const milestone of effort.milestones ?? []) {
    if (milestone.state !== "done") expanded.add(milestone.subject);
  }
  if (focus) {
    const phase = effort.phases.find((row) => row.subject === focus);
    if (phase?.milestone) expanded.add(phase.milestone);
  }
  return expanded;
}
