<script lang="ts">
  import { onMount, tick } from "svelte";
  import {
    beginWrite,
    writeBody,
    writeChoices,
    writePath,
    type ConfirmChoice,
    type PendingWrite,
  } from "./actions";
  import { getJson, postJson } from "./api";
  import {
    backlogHref,
    closeDetail,
    detailTarget,
    journalHref,
    needsHref,
    openHash,
    phaseHref,
    recordHref,
    requirementHref,
    taskHref,
    type DetailTarget,
  } from "./detail";
  import { detailView, evidenceBoard, scanNeeds, taskBoard } from "./detailView";
  import { linkifyText, type RefContext } from "./links";
  import { renderMarkdown } from "./markdown";
  import { buildPhaseChrome } from "./phaseChrome";
  import TaskGraphBoard from "./TaskGraphBoard.svelte";
  import { buildWaveGraph } from "./taskGraph";
  import {
    defaultPhase,
    filteredTasks,
    resolvedPhase,
    STATUS_TABS,
    tabCounts,
    visibleEfforts,
  } from "./efforts";
  import {
    groupPhasesByMilestone,
    initialExpandedMilestones,
  } from "./milestones";
  import { startTokenPoller } from "./poll";
  import { currentRoute, routeLabel, type Route } from "./router";
  import { filterJournal, openBacklog, orderedJournal } from "./side";
  import { applyTheme, DEFAULT_THEME, toggle, type Theme } from "./theme";
  import type {
    EffortView,
    JournalResponse,
    Snapshot,
    StatusTab,
  } from "./types";

  function statusLabel(status: string): string {
    const known: Record<string, string> = {
      done: "Done",
      running: "Running",
      ready: "Ready",
      waiting: "Waiting",
      withdrawn: "Withdrawn",
    };
    return known[status] ?? status.replace(/_/g, " ");
  }

  function escHtml(value: string): string {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const JOURNAL_TEASER_KINDS = new Set(["repair", "evaluate"]);

  let theme: Theme = $state(DEFAULT_THEME);
  let route: Route = $state(currentRoute());

  let snapshot: Snapshot | null = $state(null);
  let loading = $state(true);
  let error = $state("");
  let pollError = $state("");

  let selectedEffort = $state("");
  /** null = follow default; "all" = every phase; else a phase subject. */
  let pinnedPhase: string | null = $state(null);
  let statusTab: StatusTab = $state("active");
  /** Effort whose status tab the user picked. Empty follows the default. */
  let tabPinnedFor = $state("");
  let showFinished = $state(false);
  /** Milestone subjects currently expanded in the Phases block. */
  let expandedMilestones: Set<string> = $state(new Set());
  /** Effort name that `expandedMilestones` was initialized for. */
  let expandedForEffort = $state("");

  let journal: JournalResponse | null = $state(null);
  let journalError = $state("");
  let journalFilter = $state("");

  let detailPayload: unknown = $state(null);
  let detailError = $state("");
  let detailLoading = $state(false);

  let pendingWrite: PendingWrite | null = $state(null);
  let confirmNote = $state("");
  let confirmLocalError = $state("");
  let writeError = $state("");
  let writeBusy = $state(false);

  $effect(() => {
    applyTheme(theme);
  });

  function setTheme(next: Theme) {
    theme = next;
  }

  function onToggleTheme() {
    setTheme(toggle(theme));
  }

  const rail = $derived(
    snapshot
      ? visibleEfforts(snapshot.efforts, showFinished)
      : { shown: [], hidden: 0 },
  );

  const effort: EffortView | null = $derived.by(() => {
    if (!snapshot) return null;
    const name =
      selectedEffort || (rail.shown[0] && rail.shown[0].effort) || "";
    return snapshot.efforts.find((view) => view.effort === name) ?? null;
  });

  const phaseSubject = $derived(
    effort ? resolvedPhase(effort, pinnedPhase) : null,
  );

  const tasks = $derived(
    effort ? filteredTasks(effort, phaseSubject, statusTab) : [],
  );

  const showNeedsInMain = $derived(
    !!effort && route.name !== "journal" && effort.needs_you.length > 0,
  );

  const counts = $derived(effort ? tabCounts(effort, phaseSubject) : null);

  $effect(() => {
    const current = effort;
    if (!current || tabPinnedFor === current.effort) return;
    const nextCounts = tabCounts(current, phaseSubject);
    if (
      current.needs_you.length > 0 &&
      nextCounts.active === 0 &&
      statusTab === "active"
    ) {
      const fallback =
        (["done", "waiting", "ready", "running", "all"] as StatusTab[]).find(
          (name) => nextCounts[name] > 0,
        ) ?? "all";
      statusTab = fallback;
    }
  });

  const hasMilestones = $derived((effort?.milestones?.length ?? 0) > 0);

  const milestoneGroups = $derived(
    effort && hasMilestones ? groupPhasesByMilestone(effort) : [],
  );

  $effect(() => {
    const current = effort;
    if (!current?.milestones?.length) {
      expandedForEffort = "";
      expandedMilestones = new Set();
      return;
    }
    if (expandedForEffort === current.effort) return;
    expandedForEffort = current.effort;
    expandedMilestones = initialExpandedMilestones(current, pinnedPhase);
  });

  const backlogItems = $derived(openBacklog(effort));

  const showJournalTeaser = $derived(
    !!effort && JOURNAL_TEASER_KINDS.has(effort.kind),
  );

  const journalOpenCount = $derived(journal ? journal.open.length : null);

  const journalEffort = $derived(
    route.name === "journal" ? (route.parts[1] ?? "") : "",
  );

  const journalItems = $derived(
    filterJournal(orderedJournal(journal), journalFilter),
  );

  const target: DetailTarget | null = $derived(detailTarget(route));

  const linkCtx: RefContext | null = $derived.by(() => {
    if (!snapshot) return null;
    const effortName =
      target?.kind === "phase"
        ? (route.parts[1] ?? effort?.effort ?? null)
        : target?.kind === "requirement"
          ? (route.parts[1] ?? effort?.effort ?? null)
          : (effort?.effort ?? selectedEffort ?? null);
    const phaseName =
      target?.kind === "phase"
        ? (route.parts[2] ?? phaseSubject)
        : target?.kind === "requirement"
          ? (route.parts[2] ?? phaseSubject)
          : phaseSubject;
    return {
      snapshot,
      effort: effortName,
      phase: phaseName,
      detail:
        detailPayload && typeof detailPayload === "object"
          ? (detailPayload as Record<string, unknown>)
          : null,
    };
  });

  function linkify(text: string): string {
    if (!linkCtx) return escHtml(text);
    return linkifyText(text, linkCtx, escHtml);
  }

  function md(body: string): string {
    return renderMarkdown(body, linkCtx);
  }

  /** Expand a milestone group when the hash names one. */
  $effect(() => {
    if (route.name !== "milestone") return;
    const effortName = route.parts[1] ?? "";
    const milestoneKey = route.parts[2] ?? "";
    if (!effortName || !milestoneKey || !snapshot) return;
    if (selectedEffort !== effortName) selectedEffort = effortName;
    const view = snapshot.efforts.find((row) => row.effort === effortName);
    if (!view) return;
    if (expandedForEffort !== effortName || !expandedMilestones.has(milestoneKey)) {
      expandedForEffort = effortName;
      const next = new Set(expandedMilestones);
      next.add(milestoneKey);
      expandedMilestones = next;
    }
    const phases = view.phases.filter((row) => row.milestone === milestoneKey);
    if (phases.length === 1 && phases[0] && pinnedPhase !== phases[0].subject) {
      pinnedPhase = phases[0].subject;
    }
  });

  const phaseTabs: string[] = $derived.by(() => {
    if (!target || target.kind !== "phase") return [];
    if (!detailPayload || typeof detailPayload !== "object") return [];
    const tabs = (detailPayload as { tabs?: unknown }).tabs;
    return Array.isArray(tabs) ? tabs.map(String) : [];
  });

  const activePhaseTab = $derived.by(() => {
    if (!target || target.kind !== "phase") return "";
    if (target.tab && phaseTabs.includes(target.tab)) return target.tab;
    return phaseTabs[0] ?? "";
  });

  const overlayChoices: ConfirmChoice[] = $derived.by(() => {
    if (!target || !detailPayload) return [];
    if (target.kind === "needs" || target.kind === "backlog") {
      return writeChoices(target.kind, detailPayload);
    }
    return [];
  });

  const overlayEffort = $derived.by(() => {
    if (!target) return "";
    if (target.kind === "needs" || target.kind === "backlog") {
      return route.parts[1] ?? "";
    }
    return "";
  });

  const overlayView = $derived.by(() => {
    if (!target || !detailPayload) return null;
    return detailView(target.kind, detailPayload, activePhaseTab);
  });

  const taskView = $derived.by(() => {
    if (!target || target.kind !== "phase" || activePhaseTab !== "tasks" || !detailPayload) {
      return null;
    }
    return taskBoard(detailPayload);
  });

  const evidenceView = $derived.by(() => {
    if (!target || target.kind !== "phase" || activePhaseTab !== "evidence" || !detailPayload) {
      return null;
    }
    return evidenceBoard(detailPayload);
  });

  const phaseChrome = $derived.by(() => {
    if (!target || target.kind !== "phase" || !detailPayload) return null;
    return buildPhaseChrome(detailPayload, {
      position: effort?.position ?? null,
    });
  });

  function openRequirement(id: string) {
    const effortName = route.parts[1] || effort?.effort || "";
    const phaseName = route.parts[2] || "";
    if (!effortName || !phaseName || !id) return;
    openHash(requirementHref(effortName, phaseName, id));
  }

  const phaseTaskGraph = $derived.by(() => {
    if (!target || target.kind !== "phase" || !detailPayload) return null;
    if (activePhaseTab !== "overview") return null;
    const detail = (detailPayload as { detail?: { tasks?: unknown } }).detail;
    const tasks = Array.isArray(detail?.tasks) ? detail.tasks : [];
    return buildWaveGraph(
      tasks.map((row) => {
        const task = row as {
          id?: string;
          subject?: string;
          title?: string;
          status?: string;
          wave?: number | null;
          depends_on?: string[];
          waits_on?: string[];
        };
        return {
          id: String(task.id || ""),
          subject: task.subject,
          title: task.title,
          status: String(task.status || ""),
          wave: task.wave,
          depends_on: task.depends_on,
          waits_on: task.waits_on,
        };
      }).filter((task) => task.id),
    );
  });

  function openGraphTask(id: string) {
    if (!id) return;
    openHash(taskHref(id));
  }

  $effect(() => {
    if (journalEffort && journalEffort !== selectedEffort) {
      selectedEffort = journalEffort;
    }
  });

  $effect(() => {
    const name =
      journalEffort || effort?.effort || "";
    if (!name) {
      journal = null;
      journalError = "";
      return;
    }
    let cancelled = false;
    journal = null;
    journalError = "";
    void getJson<JournalResponse>(
      `journal?effort=${encodeURIComponent(name)}`,
    )
      .then((data) => {
        if (!cancelled) {
          journal = data;
          journalError = "";
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          journal = null;
          journalError = err instanceof Error ? err.message : String(err);
        }
      });
    return () => {
      cancelled = true;
    };
  });

  $effect(() => {
    const next = target;
    if (!next) {
      detailPayload = null;
      detailError = "";
      detailLoading = false;
      cancelConfirm();
      writeError = "";
      return;
    }
    let cancelled = false;
    detailPayload = null;
    detailError = "";
    detailLoading = true;
    cancelConfirm();
    writeError = "";
    void getJson<unknown>(next.apiPath)
      .then((data) => {
        if (!cancelled) {
          detailPayload = data;
          detailError = "";
          detailLoading = false;
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          detailPayload = null;
          detailError = err instanceof Error ? err.message : String(err);
          detailLoading = false;
        }
      });
    return () => {
      cancelled = true;
    };
  });

  function cancelConfirm() {
    pendingWrite = null;
    confirmNote = "";
    confirmLocalError = "";
    writeBusy = false;
  }

  function openConfirm(choice: ConfirmChoice) {
    if (!target || (target.kind !== "needs" && target.kind !== "backlog")) {
      return;
    }
    const effortName = overlayEffort;
    if (!effortName || !detailPayload) return;
    const pending = beginWrite(target.kind, effortName, detailPayload, choice);
    if (!pending) return;
    pendingWrite = pending;
    confirmNote = "";
    confirmLocalError = "";
    writeError = "";
  }

  async function submitConfirm() {
    if (!pendingWrite || writeBusy) return;
    if (pendingWrite.noteRequired && !confirmNote.trim()) {
      confirmLocalError = "Note required for this action";
      return;
    }
    confirmLocalError = "";
    writeBusy = true;
    const body = writeBody(pendingWrite, confirmNote);
    const path = writePath(pendingWrite);
    try {
      await postJson<{ ok: boolean }>(path, body);
      cancelConfirm();
      writeError = "";
      closeDetail();
      try {
        const next = await getJson<Snapshot>("snapshot");
        applySnapshot(next);
      } catch {
        /* poller will catch up */
      }
    } catch (err: unknown) {
      writeError = err instanceof Error ? err.message : String(err);
      writeBusy = false;
    }
  }

  function selectEffort(name: string) {
    selectedEffort = name;
    pinnedPhase = null;
    statusTab = "active";
    tabPinnedFor = "";
  }

  function chooseTab(name: StatusTab) {
    statusTab = name;
    tabPinnedFor = effort?.effort ?? "";
  }

  function selectPhase(targetPhase: string) {
    if (!effort) return;
    if (targetPhase === "all") {
      pinnedPhase = "all";
      return;
    }
    pinnedPhase = targetPhase === defaultPhase(effort) ? null : targetPhase;
  }

  function openPhase(subject: string) {
    if (!effort) return;
    openHash(phaseHref(effort.effort, subject));
  }

  function toggleMilestone(key: string) {
    const next = new Set(expandedMilestones);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    expandedMilestones = next;
  }

  function activatePhase(subject: string) {
    if (phaseSubject === subject) openPhase(subject);
    else selectPhase(subject);
  }

  function milestoneMeta(state: string, done: number, total: number): string {
    const label = String(state || "").replace(/_/g, " ");
    return [label, `${done}/${total}`].filter(Boolean).join(" · ");
  }

  function selectPhaseTab(tab: string) {
    if (!effort || !target || target.kind !== "phase") return;
    const effortName = route.parts[1];
    const phaseName = route.parts[2];
    if (!effortName || !phaseName) return;
    openHash(phaseHref(effortName, phaseName, tab));
  }

  function applySnapshot(data: Snapshot) {
    snapshot = data;
    loading = false;
    error = "";
    pollError = "";
    if (!selectedEffort) {
      const { shown } = visibleEfforts(data.efforts, showFinished);
      if (shown[0]) selectedEffort = shown[0].effort;
    }
  }

  onMount(() => {
    const sync = () => (route = currentRoute());
    window.addEventListener("hashchange", sync);

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "t" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        const el = event.target;
        if (
          el instanceof HTMLElement &&
          el.closest("input, textarea, select, [contenteditable='true']")
        ) {
          return;
        }
        if (pendingWrite || detailTarget(currentRoute())) return;
        event.preventDefault();
        onToggleTheme();
        return;
      }
      if (event.key !== "Escape") return;
      if (pendingWrite) {
        cancelConfirm();
        return;
      }
      const current = currentRoute();
      if (detailTarget(current)) {
        closeDetail();
        return;
      }
      if (current.name === "journal") {
        openHash("");
      }
    };
    window.addEventListener("keydown", onKey);

    const poller = startTokenPoller({
      onSnapshot: applySnapshot,
      onError: (message) => {
        if (loading) {
          loading = false;
          error = message;
        } else {
          pollError = message;
        }
      },
    });

    return () => {
      poller.stop();
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("keydown", onKey);
    };
  });

  let restoreFocus: HTMLElement | null = null;
  let focusLock = "";

  $effect(() => {
    const key = pendingWrite ? "confirm" : target ? `detail:${target.kind}` : "";
    if (key === focusLock) return;
    const prev = focusLock;
    focusLock = key;
    if (!key) {
      const back = restoreFocus;
      restoreFocus = null;
      if (prev) queueMicrotask(() => back?.focus());
      return;
    }
    if (!prev) {
      const active = document.activeElement;
      if (active instanceof HTMLElement) restoreFocus = active;
    }
    void tick().then(() => {
      const selector = pendingWrite
        ? "[data-confirm-note], [data-confirm-cancel]"
        : '[data-act="close-detail"]';
      document.querySelector<HTMLElement>(selector)?.focus();
    });
  });
</script>

{#snippet needsRows(view: EffortView)}
  {#each view.needs_you as item (item.id)}
    {@const scan = scanNeeds(item)}
    <button
      type="button"
      class="lrow needs-row clickable"
      class:has-place={scan.place.length > 0}
      data-needs={item.id}
      onclick={(e) => {
        const anchor = (e.target as HTMLElement | null)?.closest?.("a[href]");
        if (anchor) {
          e.preventDefault();
          e.stopPropagation();
          openHash(anchor.getAttribute("href") || "");
          return;
        }
        openHash(needsHref(view.effort, item.id));
      }}
    >
      <span class="kind">{scan.kind}</span>
      {#if scan.place}<span class="where">{scan.place}</span>{/if}
      <span class="text">{@html linkify(scan.claim)}</span>
    </button>
  {/each}
{/snippet}

<div class="app" inert={target || pendingWrite ? true : undefined}>
  <header class="topbar">
    <div class="brand">orchestra <span class="brand-sub">dashboard</span></div>
    <div class="crumbs" aria-live="polite">{routeLabel(route)}</div>
    <div class="top-actions">
      <button
        type="button"
        class="theme-switch"
        data-act="theme"
        role="switch"
        aria-checked={theme === "dark"}
        title="Theme (t)"
        onclick={onToggleTheme}
      >
        <span class="theme-track" aria-hidden="true"><span class="theme-thumb"></span></span>
        Dark
      </button>
    </div>
  </header>

  <div class="layout">
    <input class="rail-toggle" id="rail-toggle" type="checkbox" />
    <nav class="rail" aria-label="Efforts">
      <h2 class="rail-heading">Efforts</h2>
      {#if loading}
        <p class="empty-note">Loading…</p>
      {:else if error}
        <p class="error-note">{error}</p>
      {:else}
        {#each rail.shown as view (view.effort)}
          <button
            type="button"
            class="effort"
            class:on={effort?.effort === view.effort}
            class:finished={view.finished}
            data-effort={view.effort}
            onclick={() => selectEffort(view.effort)}
          >
            <span
              class="dot"
              style:background={view.needs_you.length
                ? "var(--warn)"
                : view.finished
                  ? "var(--faint)"
                  : "var(--accent)"}
            ></span>
            <span>
              <span class="name">{view.effort}</span>
              <span class="sub" class:warn={view.needs_you.length > 0}>
                {view.kind}{#if view.finished} · finished{/if}{#if view.needs_you.length}
                  · {view.needs_you.length} needs you{/if}
              </span>
            </span>
          </button>
        {/each}
        {#if rail.hidden > 0 || showFinished}
          <button
            type="button"
            class="show-finished"
            class:on={showFinished}
            data-act="show-finished"
            aria-pressed={showFinished}
            title="Show finished efforts"
            onclick={() => (showFinished = !showFinished)}
          >
            {showFinished ? "Hide finished" : `${rail.hidden} finished`}
          </button>
        {/if}
      {/if}
    </nav>

    <main class="main" data-route={route.name}>
      {#if route.name === "journal"}
        <section class="journal-screen" data-journal-screen>
          <header class="journal-bar">
            <button
              type="button"
              class="back"
              data-act="close-journal"
              onclick={() => openHash("")}
            >
              Back
            </button>
            <span class="journal-title">
              Journal{#if journalEffort}
                {" "}· {journalEffort}{/if}
            </span>
          </header>
          <input
            class="field"
            type="search"
            data-journal-filter
            aria-label="Filter journal"
            placeholder="Filter by subject or text"
            bind:value={journalFilter}
          />
          {#if journalError}
            <p class="error-note">{journalError}</p>
          {:else if !journal}
            <p class="empty-note">Loading journal…</p>
          {:else if journalItems.length === 0}
            <p class="empty-note">No journal entries</p>
          {:else}
            <div class="journal-list" data-journal-list>
              {#each journalItems as item (item.id)}
                <button
                  type="button"
                  class="lrow clickable"
                  data-journal="{item.id}"
                  data-record-type={item.record_type}
                  onclick={() => openHash(recordHref(item.id))}
                >
                  <span class="kind">{item.record_type}</span>
                  <span class="text">{item.subject || item.text || ""}</span>
                  {#if item.text && item.subject && item.text !== item.subject}
                    <span class="meta">{item.text}</span>
                  {/if}
                </button>
              {/each}
            </div>
          {/if}
        </section>
      {:else if effort}
        <header class="effort-head">
          <h1 class="effort-title" data-effort-title>{effort.effort}</h1>
          <p class="goal" data-goal>{effort.goal}</p>
        </header>

        {#if showNeedsInMain}
          <section class="needs-block" data-side-needs>
            <h2 class="ptitle">
              Needs you <span class="count">{effort.needs_you.length}</span>
            </h2>
            {@render needsRows(effort)}
          </section>
        {/if}

        {#if effort.phases.length}
          {#if hasMilestones}
            <section class="phases-block" data-phase-control data-phases-block>
              <h2 class="milestones-heading">Milestones</h2>
              {#each milestoneGroups as group (group.key)}
                <div
                  class="milestone"
                  class:open={expandedMilestones.has(group.key)}
                  data-milestone={group.key || "ungrouped"}
                >
                  <button
                    type="button"
                    class="milestone-head"
                    aria-expanded={expandedMilestones.has(group.key)}
                    data-milestone-toggle={group.key || "ungrouped"}
                    onclick={() => toggleMilestone(group.key)}
                  >
                    <span class="milestone-chevron" aria-hidden="true"
                      >{expandedMilestones.has(group.key) ? "▼" : "▶"}</span
                    >
                    <span class="milestone-title">{group.title}</span>
                    {#if group.milestone}
                      <span class="milestone-meta"
                        >{milestoneMeta(
                          group.milestone.state,
                          group.milestone.done,
                          group.milestone.total,
                        )}</span
                      >
                    {:else}
                      <span class="milestone-meta"
                        >{group.phases.length} phase{group.phases.length === 1
                          ? ""
                          : "s"}</span
                      >
                    {/if}
                  </button>
                  {#if expandedMilestones.has(group.key)}
                    <div class="milestone-phases">
                      {#each group.phases as phase (phase.subject)}
                        <button
                          type="button"
                          class="phase-row"
                          class:on={phaseSubject === phase.subject}
                          class:done={phase.state === "done"}
                          class:live={phase.state === "in_progress"}
                          data-phase={phase.subject}
                          aria-current={phaseSubject === phase.subject ? "true" : undefined}
                          title={phaseSubject === phase.subject
                            ? "Selected. Press again to open."
                            : "Show this phase"}
                          onclick={() => activatePhase(phase.subject)}
                        >
                          <span class="name"
                            >{phase.title || phase.subject}</span
                          >
                          <span class="cnt">{phase.done}/{phase.total}</span>
                        </button>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/each}
              <button
                type="button"
                class="seg phases-all"
                class:on={phaseSubject === null}
                data-phase="all"
                onclick={() => selectPhase("all")}
              >
                All phases
              </button>
            </section>
          {:else}
            <div class="stepper" data-phase-control>
              {#each effort.phases
                .slice()
                .sort((a, b) => a.ordinal - b.ordinal) as phase (phase.subject)}
                <button
                  type="button"
                  class="seg"
                  class:on={phaseSubject === phase.subject}
                  class:live={phase.state === "in_progress"}
                  data-phase={phase.subject}
                  aria-current={phaseSubject === phase.subject ? "true" : undefined}
                  title={phaseSubject === phase.subject
                    ? "Selected. Press again to open."
                    : "Show this phase"}
                  onclick={() => activatePhase(phase.subject)}
                >
                  {phase.title || phase.subject}
                  <span class="cnt">{phase.done}/{phase.total}</span>
                </button>
              {/each}
              <button
                type="button"
                class="seg"
                class:on={phaseSubject === null}
                data-phase="all"
                onclick={() => selectPhase("all")}
              >
                All phases
              </button>
            </div>
          {/if}
        {/if}

        <div class="tabs" data-status-tabs>
          {#each STATUS_TABS as tab}
            <button
              type="button"
              class="tab"
              class:on={statusTab === tab.name}
              data-tab={tab.name}
              aria-current={statusTab === tab.name ? "true" : undefined}
              onclick={() => chooseTab(tab.name)}
            >
              <b>{tab.label}</b>
              {#if counts}
                <span class="n">({counts[tab.name]})</span>
              {/if}
            </button>
          {/each}
        </div>

        <div class="table" data-task-table style="--cols: 118px 1fr">
          <div class="trow thead">
            <span>Status</span>
            <span>Task</span>
          </div>
          {#if tasks.length === 0}
            <p class="empty-note">No tasks in this tab.</p>
          {:else}
            {#each tasks as task (task.id)}
              <button
                type="button"
                class="trow task clickable"
                data-task={task.id}
                data-phase-of={task.phase}
                onclick={() => openHash(taskHref(task.id))}
              >
                <span class="st {task.status}">{statusLabel(task.status)}</span>
                <span class="title">{task.title || task.subject}</span>
              </button>
            {/each}
          {/if}
        </div>
      {:else if !loading && !error}
        <p class="empty-note">No efforts in this store.</p>
      {/if}
    </main>

    <aside class="side" aria-label="Details">
      {#if effort}
        {#if !showNeedsInMain}
          <section
            class="panel"
            class:warn={effort.needs_you.length > 0}
            data-side-needs
          >
            <h2 class="ptitle">
              Needs you
              {#if effort.needs_you.length}
                <span class="count">{effort.needs_you.length}</span>
              {/if}
            </h2>
            {#if effort.needs_you.length === 0}
              <p class="empty-note">Nothing needs you</p>
            {:else}
              {@render needsRows(effort)}
            {/if}
          </section>
        {/if}

        {#if showJournalTeaser}
          <section class="panel" data-side-journal-teaser>
            <a
              class="lrow clickable"
              data-journal-teaser
              href={journalHref(effort.effort)}
              onclick={(e) => {
                e.preventDefault();
                openHash(journalHref(effort.effort));
              }}
            >
              <span class="kind accent">journal</span>
              <span class="text">
                Journal{#if journalOpenCount !== null && journalOpenCount > 0}
                  {" "}{journalOpenCount} open{/if}
              </span>
              {#if journalError}
                <span class="meta">{journalError}</span>
              {/if}
            </a>
          </section>
        {/if}

        <section class="panel" data-side-backlog>
          <h2 class="ptitle">
            Backlog
            {#if backlogItems.length}
              <span class="count">{backlogItems.length}</span>
            {/if}
          </h2>
          {#if backlogItems.length === 0}
            <p class="empty-note">No backlog</p>
          {:else}
            {#each backlogItems as item (item.id)}
              <button
                type="button"
                class="lrow clickable"
                data-backlog={item.id}
                onclick={() => openHash(backlogHref(effort.effort, item.id))}
              >
                <span class="text">{item.text || item.subject}</span>
                {#if item.subject && item.subject !== item.text}
                  <span class="meta">{item.subject}</span>
                {/if}
              </button>
            {/each}
          {/if}
        </section>
      {/if}
    </aside>
    <label class="rail-toggle-label" for="rail-toggle">Efforts</label>
  </div>

  <footer class="statusbar">
    {#if pollError}
      {pollError}
    {:else if snapshot}
      Live
    {/if}
  </footer>
</div>

{#if target}
  <div
    class="overlay"
    data-detail={target.kind}
    role="dialog"
    aria-modal="true"
    aria-labelledby="overlay-who"
    tabindex="-1"
    inert={pendingWrite ? true : undefined}
  >
    <header class="overlay-bar">
      <button type="button" class="back" data-act="close-detail" onclick={closeDetail}>
        Back
      </button>
      <div class="overlay-title">
        <span class="who" id="overlay-who">{overlayView?.who ?? target.kind}</span>
        {#if overlayView?.ctx}
          <span class="ctx">{overlayView.ctx}</span>
        {/if}
      </div>
    </header>
    <div class="overlay-body">
      {#if detailLoading}
        <p class="empty-note">Loading…</p>
      {:else if detailError}
        <p class="error-note">{detailError}</p>
      {:else if detailPayload && overlayView}
        {#if target.kind === "phase" && phaseTabs.length}
          <div class="overlay-tabs" data-phase-tabs>
            {#each phaseTabs as tab (tab)}
              <button
                type="button"
                class="tab"
                class:on={activePhaseTab === tab}
                data-phase-tab={tab}
                onclick={() => selectPhaseTab(tab)}
              >
                {tab}
              </button>
            {/each}
          </div>
        {/if}
        {#if phaseChrome}
          <div class="phase-chrome" data-phase-chrome>
            <div class="chips" data-detail-chips data-phase-chips>
              {#each phaseChrome.chips as chip (chip.label)}
                <span class="chip {chip.tone || ''}">{chip.label}</span>
              {/each}
            </div>
            <p class="phase-next" data-phase-next title={phaseChrome.nextAction}>
              <span class="phase-next-label">Next</span>
              {phaseChrome.nextAction}
            </p>
            {#if phaseChrome.requirements.length}
              <div class="phase-reqs" data-phase-reqs>
                {#each phaseChrome.requirements as req (req.id)}
                  <button
                    type="button"
                    class="phase-req"
                    class:ok={req.status === "pass" || req.status === "verified"}
                    class:warn={req.status === "fail"}
                    data-phase-req={req.id}
                    title={req.text || req.id}
                    onclick={() => openRequirement(req.id)}
                  >
                    <span class="req-id">{req.id}</span>
                    <span class="req-meta">{req.status}</span>
                  </button>
                {/each}
              </div>
            {:else}
              <p class="phase-reqs-empty" data-phase-reqs-empty>No requirements yet</p>
            {/if}
          </div>
        {/if}
        {#if phaseTaskGraph?.show}
          <TaskGraphBoard
            graph={phaseTaskGraph}
            onselect={openGraphTask}
            colorMode={theme}
          />
        {/if}
        {#if taskView}
          <div class="task-board" data-task-board data-detail-section="Tasks">
            {#if taskView.length}
              <div class="task-rows">
                {#each taskView as row (row.id)}
                  <button
                    type="button"
                    class="task-row"
                    class:ok={row.tone === "ok"}
                    class:warn={row.tone === "warn"}
                    class:accent={row.tone === "accent"}
                    data-phase-task={row.id}
                    onclick={() => openGraphTask(row.id)}
                  >
                    <span class="task-status">{row.status}</span>
                    <span class="task-wave">{row.wave}</span>
                    <span class="task-title">{row.title}</span>
                  </button>
                {/each}
              </div>
            {:else}
              <p class="empty-note">No tasks on this phase.</p>
            {/if}
          </div>
        {/if}
        {#if evidenceView}
          <div class="evidence-board" data-evidence-board>
            {#if evidenceView.facts.length}
              <div class="chips" data-evidence-facts>
                {#each evidenceView.facts as fact (fact.label)}
                  <span class="chip">
                    <span class="fact-k">{fact.label}</span>
                    {fact.value}
                  </span>
                {/each}
              </div>
            {/if}
            {#if evidenceView.rows.length}
              <div class="evidence-reqs" data-evidence-reqs>
                {#each evidenceView.rows as row (row.id)}
                  <button
                    type="button"
                    class="evidence-req"
                    class:ok={row.tone === "ok"}
                    class:warn={row.tone === "warn"}
                    data-evidence-req={row.id}
                    onclick={() => openRequirement(row.id)}
                  >
                    <span class="evidence-id">{row.id}</span>
                    <span class="evidence-status">{row.status}</span>
                    <span class="evidence-tasks">{row.tasks}</span>
                    <span class="evidence-copy">
                      <span class="evidence-text">{row.text}</span>
                      {#if row.next}
                        <span class="evidence-next">next {row.next}</span>
                      {/if}
                    </span>
                  </button>
                {/each}
              </div>
            {:else if !evidenceView.facts.length}
              <p class="empty-note">No evidence summary.</p>
            {/if}
          </div>
        {/if}
        {#if !phaseChrome && overlayView.chips.length}
          <div class="chips" data-detail-chips>
            {#each overlayView.chips as chip (chip.label)}
              <span class="chip {chip.tone || ''}">{chip.label}</span>
            {/each}
          </div>
        {/if}
        {#if writeError && !pendingWrite}
          <p class="write-error" data-write-error>{writeError}</p>
        {/if}
        {#each overlayView.sections as section, index (section.title + index)}
          {#if section.title}
            <div class="section-title" data-section-card>{section.title}</div>
          {/if}
          <div
            class="md section-card"
            data-detail-section={section.title || "body"}
          >{@html md(section.body)}</div>
        {/each}
        {#if overlayChoices.length}
          <div class="overlay-actions" data-write-actions>
            {#each overlayChoices as choice (choice.action)}
              <button
                type="button"
                class="btn"
                class:primary={choice.action === "accept"}
                data-write-action={choice.action}
                onclick={() => openConfirm(choice)}
              >
                {choice.label}
              </button>
            {/each}
          </div>
        {/if}
        <!-- Probe text for acceptances; not shown as a JSON dump. -->
        <pre data-detail-payload class="sr-only">{overlayView.probe}</pre>
      {/if}
    </div>
    <footer class="overlay-keys">
      <span><b>Esc</b> back</span>
    </footer>
  </div>
{/if}

{#if pendingWrite}
  <div
    class="modal-layer"
    data-confirm
    role="presentation"
  >
    <button
      type="button"
      class="modal-scrim"
      aria-label="Cancel"
      onclick={cancelConfirm}
    ></button>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" tabindex="-1">
      <h3 id="confirm-title">{pendingWrite.label}?</h3>
      <p class="hint">
        {#if pendingWrite.action === "accept"}
          Accepting risk records that you saw this and clears it from Needs you.
        {:else}
          This records your decision on this item.
        {/if}
        {pendingWrite.noteRequired ? "A note is required." : "A note is optional."}
        Esc cancels.
      </p>
      {#if pendingWrite.kind === "needs"}
        <label class="field-label" for="confirm-note">Note</label>
        <input
          id="confirm-note"
          class="field"
          type="text"
          data-confirm-note
          placeholder="What should the record say?"
          bind:value={confirmNote}
          onkeydown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void submitConfirm();
            }
          }}
        />
      {/if}
      {#if confirmLocalError}
        <p class="err" data-confirm-local-error>{confirmLocalError}</p>
      {/if}
      {#if writeError}
        <p class="err" data-write-error>{writeError}</p>
      {/if}
      <div class="row">
        <button type="button" class="btn" data-confirm-cancel onclick={cancelConfirm}>
          Cancel
        </button>
        <button
          type="button"
          class="btn primary"
          data-confirm-submit
          disabled={writeBusy ||
            (pendingWrite.noteRequired && confirmNote.trim().length === 0)}
          onclick={() => void submitConfirm()}
        >
          {pendingWrite.label}
        </button>
      </div>
    </div>
  </div>
{/if}
