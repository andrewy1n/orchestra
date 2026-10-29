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

/** Keep items whose subject or text contains *needle* (case-insensitive). */
export function filterJournal(
	items: JournalItem[],
	needle: string,
): JournalItem[] {
	const n = needle.trim().toLowerCase();
	if (!n) return items.slice();
	return items.filter(
		(item) =>
			item.subject.toLowerCase().includes(n) ||
			(item.text ?? "").toLowerCase().includes(n),
	);
}

/** Open backlog items for an effort (snapshot already prefers open). */
export function openBacklog(effort: EffortView | null): BacklogItem[] {
	if (!effort?.backlog) return [];
	return effort.backlog.filter((item) => item.status === "open");
}
