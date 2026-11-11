export function firstSentence(text: string, max = 110): string {
	const flat = text.replace(/\s+/g, " ").trim();
	const end = flat.search(/[.!?](\s|$)/);
	const sentence = end >= 0 ? flat.slice(0, end + 1) : flat;
	if (sentence.length <= max) return sentence;
	const cut = sentence.slice(0, max);
	const space = cut.lastIndexOf(" ");
	return `${(space > max / 2 ? cut.slice(0, space) : cut).replace(/[,;:\s]+$/, "")}…`;
}

export function relativeTime(
	iso: string | null | undefined,
	now = Date.now(),
): string {
	const then = iso ? Date.parse(iso) : Number.NaN;
	if (Number.isNaN(then)) return "a while ago";
	const minutes = Math.floor(Math.max(now - then, 0) / 60_000);
	if (minutes < 1) return "just now";
	if (minutes < 60) return `${minutes} min ago`;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
	const days = Math.floor(hours / 24);
	return `${days} ${days === 1 ? "day" : "days"} ago`;
}
