/** Snapshot shapes from `GET /api/snapshot` (spike / dashboard.web contract). */

export interface NeedsYouItem {
  kind: string;
  id: string;
  subject: string;
  text: string;
  phase?: string;
  requirement?: string;
  status?: string;
  next?: string;
  result?: string;
  revision?: string;
  task_id?: string;
  record_type?: string;
}

export interface TaskRow {
  id: string;
  subject: string;
  title: string;
  phase: string;
  status: string;
  wave?: number | null;
  assignee?: string;
  size?: string;
  estimate_minutes?: number | null;
  executor?: string;
  attempts?: number;
  retry_budget?: number;
}

export interface PhaseRow {
  subject: string;
  title: string;
  ordinal: number;
  state: string;
  done: number;
  total: number;
  awaiting_signoff?: boolean;
  sitting?: string;
  suite?: string;
  milestone?: string;
  milestone_title?: string;
}

export interface EffortView {
  effort: string;
  goal: string;
  kind: string;
  finished: boolean;
  release_ready?: boolean;
  position?: string;
  phases: PhaseRow[];
  tasks: TaskRow[];
  needs_you: NeedsYouItem[];
  milestones?: unknown[];
  backlog?: unknown[];
}

export interface Snapshot {
  token: string;
  generated_at?: string;
  store?: string;
  efforts: EffortView[];
}

export type StatusTab =
  | "active"
  | "running"
  | "ready"
  | "waiting"
  | "done"
  | "all";

/** Poll interval for `GET /api/token` (~2s per design). */
export const TOKEN_POLL_MS = 2000;
