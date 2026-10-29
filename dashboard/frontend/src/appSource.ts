import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

const FILES = [
	"App.svelte",
	"lib/screens/EffortRail.svelte",
	"lib/screens/Home.svelte",
	"lib/screens/Journal.svelte",
	"lib/screens/NeedsRows.svelte",
	"lib/screens/Overlay.svelte",
	"lib/screens/PhaseOverlay.svelte",
	"lib/screens/ConfirmModal.svelte",
	"lib/screens/SideRail.svelte",
	"lib/state/polling.svelte.ts",
	"lib/state/journal.svelte.ts",
	"lib/state/overlay.svelte.ts",
	"lib/state/route.svelte.ts",
];

export const appSource = FILES.map((file) =>
	readFileSync(path.join(here, file), "utf8"),
).join("\n");
