/**
 * Shared structured chrome for every phase overlay tab.
 */

export interface PhaseChromeChip {
	label: string;
	tone?: "ok" | "warn" | "accent" | "";
}

export interface PhaseReqChip {
	id: string;
	status: string;
	text: string;
}

export interface PhaseWaveRow {
	wave: string;
	total: number;
	done: number;
}

export interface PhaseChromeModel {
	chips: PhaseChromeChip[];
	progressLabel: string;
	nextAction: string;
	requirements: PhaseReqChip[];
	waves: PhaseWaveRow[];
}

function obj(value: unknown): Record<string, unknown> {
	return value && typeof value === "object" && !Array.isArray(value)
		? (value as Record<string, unknown>)
		: {};
}

function str(value: unknown): string {
	return value == null ? "" : String(value);
}

/**
 * Build chrome from GET /api/phase payload. Safe for phases with no
 * specification or evidence — missing blocks become empty arrays / fallbacks.
 */
export function buildPhaseChrome(payload: unknown): PhaseChromeModel {
	const root = obj(payload);
	const detail = obj(root.detail);
	const state = str(detail.state);
	const tasks = Array.isArray(detail.tasks) ? detail.tasks : [];
	const done = tasks.filter((row) => obj(row).status === "done").length;
	const total = tasks.length;

	const chips: PhaseChromeChip[] = [];
	if (state) {
		chips.push({
			label: state.replace(/_/g, " "),
			tone: state === "done" ? "ok" : state === "in_progress" ? "accent" : "",
		});
	}
	chips.push({ label: `${done}/${total} tasks` });
	if (detail.awaiting_signoff) {
		chips.push({ label: "awaiting sign-off", tone: "warn" });
	}

	const progressLabel =
		total === 0 ? "No tasks yet" : `${done} of ${total} tasks done`;

	const fromDetail =
		str(detail.next_action) || str(detail.position) || str(detail.next_step);
	const nextAction =
		fromDetail ||
		(state === "done"
			? "Phase complete"
			: total === 0
				? "No tasks planned yet"
				: done < total
					? "Continue ready work"
					: "Review and close");

	const evidence = obj(detail.evidence);
	const reqRows = Array.isArray(evidence.requirements)
		? (evidence.requirements as unknown[])
		: [];
	const requirements: PhaseReqChip[] = reqRows
		.map((row) => {
			const item = obj(row);
			const check = obj(item.latest_check);
			const id = str(item.id);
			if (!id) return null;
			return {
				id,
				status: str(check.result) || str(item.status) || "—",
				text: str(item.text),
			};
		})
		.filter((row): row is PhaseReqChip => row != null);

	const byWave = new Map<string, { total: number; done: number }>();
	for (const row of tasks) {
		const item = obj(row);
		const waveKey =
			item.wave == null || item.wave === "" ? "—" : String(item.wave);
		const bucket = byWave.get(waveKey) ?? { total: 0, done: 0 };
		bucket.total += 1;
		if (str(item.status) === "done") bucket.done += 1;
		byWave.set(waveKey, bucket);
	}
	const waves: PhaseWaveRow[] = [...byWave.entries()]
		.sort(([a], [b]) => {
			if (a === "—") return 1;
			if (b === "—") return -1;
			return Number(a) - Number(b);
		})
		.map(([wave, counts]) => ({
			wave,
			total: counts.total,
			done: counts.done,
		}));

	return {
		chips,
		progressLabel,
		nextAction,
		requirements,
		waves,
	};
}
