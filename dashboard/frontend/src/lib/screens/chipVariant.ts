import type { BadgeVariant } from "$lib/components/ui/badge/index.js";

export function chipVariant(tone: string | undefined): BadgeVariant {
	if (tone === "ok") return "secondary";
	if (tone === "warn") return "destructive";
	if (tone === "accent") return "default";
	return "outline";
}
