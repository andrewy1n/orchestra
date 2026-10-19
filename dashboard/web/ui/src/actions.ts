/**
 * Confirm-before-write helpers for Needs you and backlog overlays.
 *
 * Action buttons open a confirm control; only that control POSTs.
 * Reject and accept keep a note field. Write errors surface on the page.
 */

export interface ConfirmChoice {
  action: string;
  label: string;
  note_required?: boolean;
}

export type WriteKind = "needs" | "backlog";

export interface PendingWrite {
  kind: WriteKind;
  effort: string;
  id: string;
  action: string;
  label: string;
  noteRequired: boolean;
  revision?: string;
}

const NOTE_REQUIRED = new Set(["reject", "accept"]);

const BACKLOG_CHOICES: ConfirmChoice[] = [
  { action: "promote", label: "Promote", note_required: false },
  { action: "dismiss", label: "Dismiss", note_required: false },
];

/** Confirm choices from a GET /api/needs payload. */
export function needsConfirmChoices(payload: unknown): ConfirmChoice[] {
  if (!payload || typeof payload !== "object") return [];
  const item = (payload as { item?: unknown }).item;
  if (!item || typeof item !== "object") return [];
  const approval = (item as { approval?: unknown }).approval;
  if (!approval || typeof approval !== "object") return [];
  const raw = (approval as { confirm_choices?: unknown }).confirm_choices;
  if (!Array.isArray(raw)) return [];
  const out: ConfirmChoice[] = [];
  for (const entry of raw) {
    if (!entry || typeof entry !== "object") continue;
    const action = String((entry as { action?: unknown }).action ?? "").trim();
    const label = String((entry as { label?: unknown }).label ?? action).trim();
    if (!action) continue;
    const noteFlag = (entry as { note_required?: unknown }).note_required;
    out.push({
      action,
      label: label || action,
      note_required:
        typeof noteFlag === "boolean" ? noteFlag : NOTE_REQUIRED.has(action),
    });
  }
  return out;
}

/** Revision the needs overlay is showing (never send @current). */
export function needsRevision(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;
  const item = (payload as { item?: unknown }).item;
  if (!item || typeof item !== "object") return undefined;
  const revision = (item as { revision?: unknown }).revision;
  if (typeof revision !== "string" || !revision.trim()) return undefined;
  return revision;
}

/** Needs you id from the detail payload. */
export function needsId(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;
  const item = (payload as { item?: unknown }).item;
  if (!item || typeof item !== "object") return undefined;
  const id = (item as { id?: unknown }).id;
  return typeof id === "string" && id ? id : undefined;
}

/** Backlog id from the detail payload. */
export function backlogId(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;
  const item = (payload as { item?: unknown }).item;
  if (!item || typeof item !== "object") return undefined;
  const id = (item as { id?: unknown }).id;
  return typeof id === "string" && id ? id : undefined;
}

/** Action buttons for a needs or backlog overlay. */
export function writeChoices(kind: WriteKind, payload: unknown): ConfirmChoice[] {
  if (kind === "needs") return needsConfirmChoices(payload);
  if (kind === "backlog") return BACKLOG_CHOICES;
  return [];
}

/** Whether the confirm note is required for this action. */
export function noteRequiredFor(
  action: string,
  choice?: ConfirmChoice,
): boolean {
  if (choice && typeof choice.note_required === "boolean") {
    return choice.note_required;
  }
  return NOTE_REQUIRED.has(action);
}

/** Build the pending confirm state for an action click. */
export function beginWrite(
  kind: WriteKind,
  effort: string,
  payload: unknown,
  choice: ConfirmChoice,
): PendingWrite | null {
  const id = kind === "needs" ? needsId(payload) : backlogId(payload);
  if (!id) return null;
  const pending: PendingWrite = {
    kind,
    effort,
    id,
    action: choice.action,
    label: choice.label,
    noteRequired: noteRequiredFor(choice.action, choice),
  };
  if (kind === "needs") {
    const revision = needsRevision(payload);
    if (revision) pending.revision = revision;
  }
  return pending;
}

/** JSON body for POST /api/needs or /api/backlog after confirm. */
export function writeBody(
  pending: PendingWrite,
  note: string,
): Record<string, string> {
  const body: Record<string, string> = {
    effort: pending.effort,
    id: pending.id,
    action: pending.action,
  };
  if (pending.kind === "needs" && pending.revision) {
    body.revision = pending.revision;
  }
  const trimmed = note.trim();
  if (trimmed) body.note = trimmed;
  return body;
}

/** API path for a pending write. */
export function writePath(pending: PendingWrite): string {
  return pending.kind === "needs" ? "needs" : "backlog";
}
