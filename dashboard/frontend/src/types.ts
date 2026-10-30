import type {
	EffortSummary,
	PhaseSummary,
	SnapshotResponse,
} from "./api-types";

export type EffortView = EffortSummary;
export type PhaseRow = PhaseSummary;
export type Snapshot = SnapshotResponse;

export type StatusTab =
	| "active"
	| "running"
	| "ready"
	| "waiting"
	| "done"
	| "all";

/** Poll interval for `GET /api/token` (~2s per design). */
export const TOKEN_POLL_MS = 2000;

export type DeepPartial<T> = T extends readonly (infer U)[]
	? DeepPartial<U>[]
	: T extends object
		? { [K in keyof T]?: DeepPartial<T[K]> }
		: T;
