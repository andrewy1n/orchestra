import type {
  BacklogItem,
  EffortView,
  JournalItem,
  JournalResponse,
} from "./types";

/** Flat journal list in `dashboard.journal.ordered` order (open, then rest). */
export function orderedJournal(data: JournalResponse | null): JournalItem[] {
  if (!data) return [];
  return data.open.concat(data.rest);
}

/** Open backlog items for an effort (snapshot already prefers open). */
export function openBacklog(effort: EffortView | null): BacklogItem[] {
  if (!effort?.backlog) return [];
  return effort.backlog.filter((item) => item.status === "open");
}
