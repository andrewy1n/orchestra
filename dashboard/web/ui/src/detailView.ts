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
    if (body) sections.push({ title: "Phase", body });
    else sections.push({ title: "Phase", body: "No overview body." });
  } else if (active === "spec") {
    sections.push({
      title: "Specification",
      body: specBody || "No specification body.",
    });
  } else if (active === "design") {
    sections.push({
      title: "Design",
      body: designBody || "No design body.",
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
    const evidence = obj(detail.evidence);
    const bits = [
      evidence.stage ? `stage: ${evidence.stage}` : "",
      evidence.weight ? `weight: ${evidence.weight}` : "",
      evidence.release_state ? `release: ${evidence.release_state}` : "",
    ].filter(Boolean);
    const reqs = Array.isArray(evidence.requirements)
      ? (evidence.requirements as unknown[])
      : [];
    const reqLines = reqs.map((row) => {
      const item = obj(row);
      const check = obj(item.latest_check);
      const result = str(check.result) || str(item.status) || "—";
      return `${str(item.id)}  ${result}  ${str(item.text)}`;
    });
    const body = [
      bits.length ? bits.join(" · ") : "",
      reqLines.length ? reqLines.join("\n") : "",
    ]
      .filter(Boolean)
      .join("\n\n");
    sections.push({
      title: "Evidence",
      body: body || "No evidence summary.",
    });
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
    const list = Array.isArray(tasks) ? tasks : [];
    const rows = list.map((row) => {
      const item = obj(row);
      return `${str(item.status) || "—"}  ${str(item.subject) || str(item.title)}`;
    });
    sections.push({
      title: "Tasks",
      body: rows.length ? rows.join("\n") : "No tasks on this phase.",
    });
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
  if (detail.wave != null) chips.push({ label: `w${detail.wave}` });
  if (detail.size) chips.push({ label: str(detail.size) });
  if (detail.estimate_minutes != null) {
    chips.push({ label: `${detail.estimate_minutes}m` });
  }
  if (detail.executor) chips.push({ label: `executor ${detail.executor}` });

  const sections: DetailSection[] = [];
  if (description) sections.push({ title: "Description", body: description });
  const deps = Array.isArray(detail.depends_on) ? detail.depends_on : [];
  const blocks = Array.isArray(detail.blocks) ? detail.blocks : [];
  const reqs = Array.isArray(detail.requirements) ? detail.requirements : [];
  const links = [
    ...deps.map((dep) => `Depends on: ${dep}`),
    ...blocks.map((dep) => `Blocks: ${dep}`),
    ...reqs.map((req) => `Requirement: ${req}`),
  ];
  if (links.length) sections.push({ title: "Links", body: links.join("\n") });

  return {
    who: subject || title,
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

function needsDetail(payload: unknown): DetailViewModel {
  const item = obj(obj(payload).item);
  const kind = str(item.kind);
  const subject = str(item.subject);
  const text = str(item.text);
  const revision = str(item.revision);
  const approval = obj(item.approval);
  const choices = Array.isArray(approval.confirm_choices)
    ? approval.confirm_choices
    : [];
  const choiceLabels = choices
    .map((row) => str(obj(row).label) || str(obj(row).action))
    .filter(Boolean);
  const sections: DetailSection[] = [
    { title: "Needs you", body: lines(text, subject) },
  ];
  if (revision) sections.push({ title: "Revision", body: revision });
  if (choiceLabels.length) {
    sections.push({ title: "confirm_choices", body: choiceLabels.join(" · ") });
  }
  return {
    who: subject || kind || "needs",
    ctx: kind,
    chips: kind ? [{ label: kind }] : [],
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
