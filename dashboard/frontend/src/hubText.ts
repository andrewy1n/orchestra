export function firstSentence(text: string, max = 110): string {
	const flat = text.replace(/\s+/g, " ").trim();
	const end = flat.search(/[.!?](\s|$)/);
	const sentence = end >= 0 ? flat.slice(0, end + 1) : flat;
	if (sentence.length <= max) return sentence;
	const cut = sentence.slice(0, max);
	const space = cut.lastIndexOf(" ");
	return `${(space > max / 2 ? cut.slice(0, space) : cut).replace(/[,;:\s]+$/, "")}…`;
}
