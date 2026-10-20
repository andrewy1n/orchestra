/**
 * Turn detail API payloads into fields the overlay can render as UI
 * (not JSON dumps).
 */

export type DetailKind =
  | "phase"
  | "task"
  | "requirement"
  | "record"
  | "needs"
  | "backlog";

export interface DetailSection {
  title: string;
  body: string;
}

export interface DetailChip {
  label: string;
  tone?: "ok" | "warn" | "accent" | "";
}

export interface DetailLink {
  label: string;
  value: string;
}

export interface DetailViewModel {
  who: string;
  ctx: string;
  chips: DetailChip[];
  sections: DetailSection[];
  /** Flattened text for [data-detail-payload] acceptance probes. */
  probe: string;
}

function obj(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function str(value: unknown): string {
  return value == null ? "" : String(value);
}

function lines(...parts: unknown[]): string {
  return parts
    .map((part) => (part == null ? "" : String(part)))
    .filter((part) => part.trim().length > 0)
    .join("\n");
}

/** Human label for a dependency that may be a string or a record. */
function refText(value: unknown): string {
  if (value && typeof value === "object") {
    const item = obj(value);
    return str(item.title) || str(item.subject) || str(item.id) || "";
  }
  return str(value);
}

function phaseDetail(payload: unknown, tab: string): DetailViewModel {
  const root = obj(payload);
  const detail = obj(root.detail);
  const title = str(detail.title) || str(detail.subject) || "phase";
  const subject = str(detail.subject);
  const state = str(detail.state);
  const effort = str(detail.effort);
  const body = str(detail.body);
  const specBody = str(detail.spec_body);
  const designBody = str(detail.design_body);
  const chips: DetailChip[] = [];
  if (state) chips.push({ label: state });
  const tasks = detail.tasks;
  if (Array.isArray(tasks)) {
    const done = tasks.filter((t) => obj(t).status === "done").length;
    chips.push({ label: `${done}/${tasks.length} tasks` });
  }
  if (detail.awaiting_signoff) chips.push({ label: "awaiting sign-off", tone: "warn" });

  const sections: DetailSection[] = [];
  const active = tab || "overview";
  if (active === "overview") {
    if (body) sections.push({ title: "Phase notes", body });
    else sections.push({ title: "Phase notes", body: "No overview notes yet." });
  } else if (active === "spec") {
    sections.push({
      title: "Specification",
      body: specBody || "No specification recorded for this phase.",
    });
  } else if (active === "design") {
    sections.push({
      title: "Design",
      body: designBody || "No design recorded for this phase.",
    });
  } else if (active === "decisions") {
    const groups = obj(root.decisions).groups;
    const fromRoot = Array.isArray(groups) ? groups : [];
    const rows: string[] = [];
    for (const group of fromRoot) {
      // Decision log groups are [title, entries[]] tuples.
      if (Array.isArray(group) && group.length >= 2) {
        const title = str(group[0]);
        if (title) rows.push(`## ${title}`);
        const entries = Array.isArray(group[1]) ? group[1] : [];
        for (const entry of entries) {
          const item = obj(entry);
          const subjectName = str(item.subject) || str(item.id);
          const choice = str(item.choice) || str(item.text);
          if (subjectName || choice) {
            rows.push(subjectName ? `${subjectName}: ${choice}` : choice);
          }
        }
        continue;
      }
      const item = obj(group);
      const subjectName = str(item.subject) || str(item.id);
      const choice = str(item.choice) || str(item.text);
      if (subjectName || choice) {
        rows.push(subjectName ? `${subjectName}: ${choice}` : choice);
      }
    }
    if (!rows.length) {
      const fromDetail = Array.isArray(detail.decisions)
        ? (detail.decisions as unknown[])
        : [];
      for (const row of fromDetail) {
        const item = obj(row);
        const subjectName = str(item.subject) || str(item.id);
        const choice = str(item.choice) || str(item.text);
        if (subjectName || choice) {
          rows.push(subjectName ? `${subjectName}: ${choice}` : choice);
        }
      }
    }
    sections.push({
      title: "Decisions",
      body: rows.length ? rows.join("\n") : "No decisions recorded.",
    });
  } else if (active === "evidence") {
    // Requirements render as the evidence board, not a markdown list.
  } else if (active === "proof") {
    const proof = obj(detail.proof);
    if (!Object.keys(proof).length) {
      sections.push({ title: "Proof", body: "No proof packet." });
    } else {
      const head = [
        proof.kind ? `kind: ${proof.kind}` : "",
        proof.revision ? `revision: ${proof.revision}` : "",
      ]
        .filter(Boolean)
        .join(" · ");
      if (head) sections.push({ title: "Proof", body: head });
      for (const key of ["look", "attention", "machine", "diff"] as const) {
        const text = str(proof[key]).trim();
        if (text) {
          sections.push({
            title: key[0].toUpperCase() + key.slice(1),
            body: text,
          });
        }
      }
    }
  } else if (active === "tasks") {
    // Tasks render as the task board, not a markdown list.
  } else {
    // Unknown tab: show overview body as fallback.
    if (body) sections.push({ title: active, body });
  }

  const tabs = Array.isArray(root.tabs) ? root.tabs.map(String) : [];
  const probe = lines(
    title,
    subject,
    state,
    body,
    specBody,
    designBody,
    ...tabs.map((name) => `"${name}"`),
    ...sections.map((section) => section.body),
  );

  return {
    who: title,
    ctx: [effort, state].filter(Boolean).join(" · "),
    chips,
    sections,
    probe,
  };
}

function taskDetail(payload: unknown): DetailViewModel {
  const detail = obj(obj(payload).detail);
  const title = str(detail.title) || str(detail.subject) || "task";
  const subject = str(detail.subject);
  const status = str(detail.status);
  const description = str(detail.description) || str(detail.body);
  const chips: DetailChip[] = [];
  if (status) {
    chips.push({
      label: status,
      tone: status === "done" ? "ok" : status === "running" ? "accent" : "",
    });
  }
  if (detail.phase) chips.push({ label: str(detail.phase) });
  if (detail.wave != null) chips.push({ label: `wave ${detail.wave}` });
  if (detail.size) chips.push({ label: str(detail.size) });
  if (detail.estimate_minutes != null) {
    chips.push({ label: `${detail.estimate_minutes} min` });
  }
  if (detail.executor) chips.push({ label: str(detail.executor) });

  const sections: DetailSection[] = [];
  if (description) sections.push({ title: "Description", body: description });
  const deps = Array.isArray(detail.depends_on) ? detail.depends_on : [];
  const blocks = Array.isArray(detail.blocks) ? detail.blocks : [];
  const reqs = Array.isArray(detail.requirements) ? detail.requirements : [];
  const links = [
    ...deps.map((dep) => `Depends on: ${refText(dep)}`),
    ...blocks.map((dep) => `Blocks: ${refText(dep)}`),
    ...reqs.map((req) => `Requirement: ${refText(req)}`),
  ];
  if (links.length) sections.push({ title: "Links", body: links.join("\n") });

  return {
    who: title,
    ctx: [str(detail.effort), str(detail.phase)].filter(Boolean).join(" · "),
    chips,
    sections: sections.length
      ? sections
      : [{ title: "Task", body: title }],
    probe: lines(title, subject, status, description, ...links),
  };
}

function requirementDetail(payload: unknown): DetailViewModel {
  const detail = obj(obj(payload).detail);
  const id = str(detail.id);
  const text = str(detail.text);
  const status = str(detail.status);
  return {
    who: id || "requirement",
    ctx: [str(detail.phase), status].filter(Boolean).join(" · "),
    chips: status ? [{ label: status }] : [],
    sections: [{ title: "Requirement", body: text || id }],
    probe: lines(id, text, status),
  };
}

function recordDetail(payload: unknown): DetailViewModel {
  const record = obj(obj(payload).record);
  const typeName = str(record.record_type);
  const subject = str(record.subject);
  const body = str(record.body);
  return {
    who: subject || typeName || "record",
    ctx: typeName,
    chips: typeName ? [{ label: typeName }] : [],
    sections: [{ title: "Record", body: body || subject }],
    probe: lines(typeName, subject, body),
  };
}

const KIND_LABELS: Record<string, string> = {
  "needs-human": "Review",
  "behavior-bug": "Bug",
  "invariant-violation": "Invariant",
  "missing-test": "Missing test",
  "blocking-question": "Question",
  "unsigned-check": "Unsigned check",
};

/** Short label for a needs-you kind or the kind prefix inside its text. */
export function humanKind(kind: string): string {
  const key = kind.trim().toLowerCase();
  return KIND_LABELS[key] ?? kind.replace(/[-_]/g, " ");
}

export interface NeedsScan {
  kind: string;
  place: string;
  claim: string;
}

/** One scan line: kind, where it sits, and the claim after the colon. */
export function scanNeeds(item: {
  kind: string;
  text?: string;
  phase?: string;
  subject?: string;
}): NeedsScan {
  const text = (item.text || "").trim();
  const match = text.match(/^(.+?)\s+on\s+([^:]+):\s*([\s\S]+)$/);
  if (match) {
    const kindBit = match[1].replace(/\s*\([^)]*\)\s*$/, "").trim();
    return {
      kind: humanKind(kindBit),
      place: match[2].trim(),
      claim: match[3].trim().replace(/\s+/g, " "),
    };
  }
  return {
    kind: humanKind(item.kind),
    place: (item.phase || "").trim(),
    claim: text || item.subject || "",
  };
}

function decisionEffect(kind: string): string {
  if (kind === "needs-human") {
    return "Accepting risk records that you saw this and clears it from Needs you. The note is stored with that decision.";
  }
  if (kind === "unsigned-check") {
    return "Signing records that you accept this check and clears it from Needs you.";
  }
  if (kind === "blocking-question" || kind === "open-question") {
    return "Approving records your answer and clears this question from Needs you. Rejecting keeps it open.";
  }
  return "This records your decision and clears the item from Needs you.";
}

function needsDetail(payload: unknown): DetailViewModel {
  const item = obj(obj(payload).item);
  const kind = str(item.kind);
  const subject = str(item.subject);
  const text = str(item.text);
  const body = str(item.body);
  const phase = str(item.phase);
  const revision = str(item.revision);
  const approval = obj(item.approval);
  const choices = Array.isArray(approval.confirm_choices)
    ? approval.confirm_choices
    : [];
  const choiceLabels = choices
    .map((row) => str(obj(row).label) || str(obj(row).action))
    .filter(Boolean);
  const scan = scanNeeds({ kind, text, phase, subject });
  const sections: DetailSection[] = [];
  if (body && body !== scan.claim) {
    sections.push({ title: "", body });
  }
  if (phase && phase !== scan.place) {
    sections.push({ title: "Phase", body: phase });
  }
  sections.push({ title: "Decision", body: decisionEffect(kind) });
  return {
    who: scan.claim || subject || "Needs you",
    ctx: [scan.kind, scan.place].filter(Boolean).join(" · "),
    chips: [],
    sections,
    probe: lines(kind, subject, text, revision, "confirm_choices", ...choiceLabels),
  };
}

function backlogDetail(payload: unknown): DetailViewModel {
  const item = obj(obj(payload).item);
  const subject = str(item.subject);
  const text = str(item.text);
  const status = str(item.status);
  const source = str(item.source);
  return {
    who: subject || "backlog",
    ctx: [status, source].filter(Boolean).join(" · "),
    chips: status ? [{ label: status }] : [],
    sections: [
      {
        title: "Backlog",
        body: lines(text, status ? `status: ${status}` : "", source ? `source: ${source}` : ""),
      },
    ],
    probe: lines(subject, text, status, `"status": "${status}"`, source),
  };
}

export interface EvidenceFact {
  label: string;
  value: string;
}

export interface EvidenceReq {
  id: string;
  status: string;
  tasks: string;
  text: string;
  next: string;
  tone: "ok" | "warn" | "";
}

export interface EvidenceBoard {
  facts: EvidenceFact[];
  rows: EvidenceReq[];
}

function reqTone(status: string): EvidenceReq["tone"] {
  if (status === "verified" || status === "pass") return "ok";
  if (status === "fail" || status === "blocked") return "warn";
  return "";
}

export interface TaskBoardRow {
  id: string;
  title: string;
  status: string;
  wave: string;
  tone: "ok" | "warn" | "accent" | "";
}

function taskTone(status: string): TaskBoardRow["tone"] {
  if (status === "done") return "ok";
  if (status === "running" || status === "ready") return "accent";
  if (status === "waiting" || status === "blocked" || status === "fail") return "warn";
  return "";
}

/** Tasks tab: one row per task, not a markdown list. */
export function taskBoard(payload: unknown): TaskBoardRow[] {
  const tasks = obj(obj(payload).detail).tasks;
  const list = Array.isArray(tasks) ? tasks : [];
  return list
    .map((row) => {
      const item = obj(row);
      const status = str(item.status);
      return {
        id: str(item.id),
        title: str(item.title) || str(item.subject) || str(item.id),
        status: status || "—",
        wave: item.wave == null || item.wave === "" ? "" : `w${item.wave}`,
        tone: taskTone(status),
      };
    })
    .filter((row) => row.id || row.title);
}

/** Evidence tab: facts and requirement rows for the board, not a text dump. */
export function evidenceBoard(payload: unknown): EvidenceBoard {
  const evidence = obj(obj(obj(payload).detail).evidence);
  const facts: EvidenceFact[] = [];
  if (evidence.stage) facts.push({ label: "stage", value: str(evidence.stage) });
  if (evidence.weight) facts.push({ label: "weight", value: str(evidence.weight) });
  if (evidence.release_state) {
    facts.push({ label: "release", value: str(evidence.release_state) });
  }
  const reqs = Array.isArray(evidence.requirements)
    ? (evidence.requirements as unknown[])
    : [];
  const rows = reqs
    .map((row) => {
      const item = obj(row);
      const id = str(item.id);
      const status = str(item.status) || str(obj(item.latest_check).result);
      const tasks =
        item.tasks == null ? "" : `${item.tasks_done ?? 0}/${item.tasks}`;
      return {
        id,
        status,
        tasks,
        text: str(item.text),
        next: str(item.next),
        tone: reqTone(status),
      };
    })
    .filter((row) => row.id || row.text);
  return { facts, rows };
}

/** Build the overlay view model for a detail kind + optional phase tab. */
export function detailView(
  kind: DetailKind,
  payload: unknown,
  tab = "",
): DetailViewModel {
  if (kind === "phase") return phaseDetail(payload, tab);
  if (kind === "task") return taskDetail(payload);
  if (kind === "requirement") return requirementDetail(payload);
  if (kind === "record") return recordDetail(payload);
  if (kind === "needs") return needsDetail(payload);
  return backlogDetail(payload);
}
