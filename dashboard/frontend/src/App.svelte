<script lang="ts">
  import { onMount } from "svelte";
  import { bindJournal, journal } from "$lib/state/journal.svelte";
  import { bindOverlay, overlay } from "$lib/state/overlay.svelte";
  import { bindPolling, polling } from "$lib/state/polling.svelte";
  import { navigation } from "$lib/state/route.svelte";
  import {
    backlogHref,
    closeDetail,
    detailTarget,
    journalHref,
    needsHref,
    openHash,
    recordHref,
    taskHref,
  } from "./detail";
  import { scanNeeds } from "./detailView";
  import { STATUS_TABS } from "./efforts";
  import { currentRoute, routeLabel } from "./router";
  import TaskGraphBoard from "./TaskGraphBoard.svelte";
  import { applyTheme, DEFAULT_THEME, type Theme, toggle } from "./theme";
  import type { EffortView } from "./types";

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

  function milestoneMeta(state: string, done: number, total: number): string {
    const label = String(state || "").replace(/_/g, " ");
    return [label, `${done}/${total}`].filter(Boolean).join(" · ");
  }

  let theme: Theme = $state(DEFAULT_THEME);

  bindPolling();
  bindJournal();
  bindOverlay();

  const effort = $derived(polling.effort);
  const target = $derived(overlay.target);
  const hasMilestones = $derived(polling.hasMilestones);

  $effect(() => {
    applyTheme(theme);
  });

  function onToggleTheme() {
    theme = toggle(theme);
  }

  onMount(() => {
    const stopRoute = navigation.listen();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "t" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        const el = event.target;
        if (
          el instanceof HTMLElement &&
          el.closest("input, textarea, select, [contenteditable='true']")
        ) {
          return;
        }
        if (overlay.pendingWrite || detailTarget(currentRoute())) return;
        event.preventDefault();
        onToggleTheme();
        return;
      }
      if (event.key !== "Escape") return;
      if (overlay.pendingWrite) {
        overlay.cancelConfirm();
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

    const stopPolling = polling.start();

    return () => {
      stopPolling();
      stopRoute();
      window.removeEventListener("keydown", onKey);
    };
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
      <span class="text">{@html overlay.linkify(scan.claim)}</span>
    </button>
  {/each}
{/snippet}

<div class="app" inert={target || overlay.pendingWrite ? true : undefined}>
  <header class="topbar">
    <div class="brand">orchestra <span class="brand-sub">dashboard</span></div>
    <div class="crumbs" aria-live="polite">{routeLabel(navigation.route)}</div>
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
      {#if polling.loading}
        <p class="empty-note">Loading…</p>
      {:else if polling.error}
        <p class="error-note">{polling.error}</p>
      {:else}
        {#each polling.rail.shown as view (view.effort)}
          <button
            type="button"
            class="effort"
            class:on={effort?.effort === view.effort}
            class:finished={view.finished}
            data-effort={view.effort}
            onclick={() => polling.selectEffort(view.effort)}
          >
            <span
              class="dot"
              style:background={view.needs_you.length
                ? "var(--warn)"
                : view.finished
                  ? "var(--faint)"
                  : "var(--brand)"}
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
        {#if polling.rail.hidden > 0 || polling.showFinished}
          <button
            type="button"
            class="show-finished"
            class:on={polling.showFinished}
            data-act="show-finished"
            aria-pressed={polling.showFinished}
            title="Show finished efforts"
            onclick={() => (polling.showFinished = !polling.showFinished)}
          >
            {polling.showFinished ? "Hide finished" : `${polling.rail.hidden} finished`}
          </button>
        {/if}
      {/if}
    </nav>

    <main class="main" data-route={navigation.route.name}>
      {#if navigation.route.name === "journal"}
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
              Journal{#if journal.effortName}
                {" "}· {journal.effortName}{/if}
            </span>
          </header>
          <input
            class="field"
            type="search"
            data-journal-filter
            aria-label="Filter journal"
            placeholder="Filter by subject or text"
            bind:value={journal.filter}
          />
          {#if journal.error}
            <p class="error-note">{journal.error}</p>
          {:else if !journal.data}
            <p class="empty-note">Loading journal…</p>
          {:else if journal.items.length === 0}
            <p class="empty-note">No journal entries</p>
          {:else}
            <div class="journal-list" data-journal-list>
              {#each journal.items as item (item.id)}
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

        {#if polling.showNeedsInMain}
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
              {#each polling.milestoneGroups as group (group.key)}
                <div
                  class="milestone"
                  class:open={polling.expandedMilestones.has(group.key)}
                  data-milestone={group.key || "ungrouped"}
                >
                  <button
                    type="button"
                    class="milestone-head"
                    aria-expanded={polling.expandedMilestones.has(group.key)}
                    data-milestone-toggle={group.key || "ungrouped"}
                    onclick={() => polling.toggleMilestone(group.key)}
                  >
                    <span class="milestone-chevron" aria-hidden="true"
                      >{polling.expandedMilestones.has(group.key) ? "▼" : "▶"}</span
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
                  {#if polling.expandedMilestones.has(group.key)}
                    <div class="milestone-phases">
                      {#each group.phases as phase (phase.subject)}
                        <button
                          type="button"
                          class="phase-row"
                          class:on={polling.phaseSubject === phase.subject}
                          class:done={phase.state === "done"}
                          class:live={phase.state === "in_progress"}
                          data-phase={phase.subject}
                          aria-current={polling.phaseSubject === phase.subject ? "true" : undefined}
                          title={polling.phaseSubject === phase.subject
                            ? "Selected. Press again to open."
                            : "Show this phase"}
                          onclick={() => polling.activatePhase(phase.subject)}
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
                class:on={polling.phaseSubject === null}
                data-phase="all"
                onclick={() => polling.selectPhase("all")}
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
                  class:on={polling.phaseSubject === phase.subject}
                  class:live={phase.state === "in_progress"}
                  data-phase={phase.subject}
                  aria-current={polling.phaseSubject === phase.subject ? "true" : undefined}
                  title={polling.phaseSubject === phase.subject
                    ? "Selected. Press again to open."
                    : "Show this phase"}
                  onclick={() => polling.activatePhase(phase.subject)}
                >
                  {phase.title || phase.subject}
                  <span class="cnt">{phase.done}/{phase.total}</span>
                </button>
              {/each}
              <button
                type="button"
                class="seg"
                class:on={polling.phaseSubject === null}
                data-phase="all"
                onclick={() => polling.selectPhase("all")}
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
              class:on={polling.statusTab === tab.name}
              data-tab={tab.name}
              aria-current={polling.statusTab === tab.name ? "true" : undefined}
              onclick={() => polling.chooseTab(tab.name)}
            >
              <b>{tab.label}</b>
              {#if polling.counts}
                <span class="n">({polling.counts[tab.name]})</span>
              {/if}
            </button>
          {/each}
        </div>

        <div class="table" data-task-table style="--cols: 118px 1fr">
          <div class="trow thead">
            <span>Status</span>
            <span>Task</span>
          </div>
          {#if polling.tasks.length === 0}
            <p class="empty-note">No tasks in this tab.</p>
          {:else}
            {#each polling.tasks as task (task.id)}
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
      {:else if !polling.loading && !polling.error}
        <p class="empty-note">No efforts in this store.</p>
      {/if}
    </main>

    <aside class="side" aria-label="Details">
      {#if effort}
        {#if !polling.showNeedsInMain}
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

        {#if polling.showJournalTeaser}
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
                Journal{#if journal.openCount !== null && journal.openCount > 0}
                  {" "}{journal.openCount} open{/if}
              </span>
              {#if journal.error}
                <span class="meta">{journal.error}</span>
              {/if}
            </a>
          </section>
        {/if}

        <section class="panel" data-side-backlog>
          <h2 class="ptitle">
            Backlog
            {#if polling.backlogItems.length}
              <span class="count">{polling.backlogItems.length}</span>
            {/if}
          </h2>
          {#if polling.backlogItems.length === 0}
            <p class="empty-note">No backlog</p>
          {:else}
            {#each polling.backlogItems as item (item.id)}
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
    {#if polling.pollError}
      {polling.pollError}
    {:else if polling.snapshot}
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
    inert={overlay.pendingWrite ? true : undefined}
  >
    <header class="overlay-bar">
      <button type="button" class="back" data-act="close-detail" onclick={closeDetail}>
        Back
      </button>
      <div class="overlay-title">
        <span class="who" id="overlay-who">{overlay.overlayView?.who ?? target.kind}</span>
        {#if overlay.overlayView?.ctx}
          <span class="ctx">{overlay.overlayView.ctx}</span>
        {/if}
      </div>
    </header>
    <div class="overlay-body">
      {#if overlay.detailLoading}
        <p class="empty-note">Loading…</p>
      {:else if overlay.detailError}
        <p class="error-note">{overlay.detailError}</p>
      {:else if overlay.detailPayload && overlay.overlayView}
        {#if target.kind === "phase" && overlay.phaseTabs.length}
          <div class="overlay-tabs" data-phase-tabs>
            {#each overlay.phaseTabs as tab (tab)}
              <button
                type="button"
                class="tab"
                class:on={overlay.activePhaseTab === tab}
                data-phase-tab={tab}
                onclick={() => overlay.selectPhaseTab(tab)}
              >
                {tab}
              </button>
            {/each}
          </div>
        {/if}
        {#if overlay.phaseChrome}
          <div class="phase-chrome" data-phase-chrome>
            <div class="chips" data-detail-chips data-phase-chips>
              {#each overlay.phaseChrome.chips as chip (chip.label)}
                <span class="chip {chip.tone || ''}">{chip.label}</span>
              {/each}
            </div>
            <p class="phase-next" data-phase-next title={overlay.phaseChrome.nextAction}>
              <span class="phase-next-label">Next</span>
              {overlay.phaseChrome.nextAction}
            </p>
            {#if overlay.phaseChrome.requirements.length}
              <div class="phase-reqs" data-phase-reqs>
                {#each overlay.phaseChrome.requirements as req (req.id)}
                  <button
                    type="button"
                    class="phase-req"
                    class:ok={req.status === "pass" || req.status === "verified"}
                    class:warn={req.status === "fail"}
                    data-phase-req={req.id}
                    title={req.text || req.id}
                    onclick={() => overlay.openRequirement(req.id)}
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
        {#if overlay.phaseTaskGraph?.show}
          <TaskGraphBoard
            graph={overlay.phaseTaskGraph}
            onselect={(id) => overlay.openGraphTask(id)}
            colorMode={theme}
          />
        {/if}
        {#if overlay.taskView}
          <div class="task-board" data-task-board data-detail-section="Tasks">
            {#if overlay.taskView.length}
              <div class="task-rows">
                {#each overlay.taskView as row (row.id)}
                  <button
                    type="button"
                    class="task-row"
                    class:ok={row.tone === "ok"}
                    class:warn={row.tone === "warn"}
                    class:accent={row.tone === "accent"}
                    data-phase-task={row.id}
                    onclick={() => overlay.openGraphTask(row.id)}
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
        {#if overlay.evidenceView}
          <div class="evidence-board" data-evidence-board>
            {#if overlay.evidenceView.facts.length}
              <div class="chips" data-evidence-facts>
                {#each overlay.evidenceView.facts as fact (fact.label)}
                  <span class="chip">
                    <span class="fact-k">{fact.label}</span>
                    {fact.value}
                  </span>
                {/each}
              </div>
            {/if}
            {#if overlay.evidenceView.rows.length}
              <div class="evidence-reqs" data-evidence-reqs>
                {#each overlay.evidenceView.rows as row (row.id)}
                  <button
                    type="button"
                    class="evidence-req"
                    class:ok={row.tone === "ok"}
                    class:warn={row.tone === "warn"}
                    data-evidence-req={row.id}
                    onclick={() => overlay.openRequirement(row.id)}
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
            {:else if !overlay.evidenceView.facts.length}
              <p class="empty-note">No evidence summary.</p>
            {/if}
          </div>
        {/if}
        {#if !overlay.phaseChrome && overlay.overlayView.chips.length}
          <div class="chips" data-detail-chips>
            {#each overlay.overlayView.chips as chip (chip.label)}
              <span class="chip {chip.tone || ''}">{chip.label}</span>
            {/each}
          </div>
        {/if}
        {#if overlay.writeError && !overlay.pendingWrite}
          <p class="write-error" data-write-error>{overlay.writeError}</p>
        {/if}
        {#each overlay.overlayView.sections as section, index (section.title + index)}
          {#if section.title}
            <div class="section-title" data-section-card>{section.title}</div>
          {/if}
          <div
            class="md section-card"
            data-detail-section={section.title || "body"}
          >{@html overlay.md(section.body)}</div>
        {/each}
        {#if overlay.overlayChoices.length}
          <div class="overlay-actions" data-write-actions>
            {#each overlay.overlayChoices as choice (choice.action)}
              <button
                type="button"
                class="btn"
                class:primary={choice.action === "accept"}
                data-write-action={choice.action}
                onclick={() => overlay.openConfirm(choice)}
              >
                {choice.label}
              </button>
            {/each}
          </div>
        {/if}
        <!-- Probe text for acceptances; not shown as a JSON dump. -->
        <pre data-detail-payload class="sr-only">{overlay.overlayView.probe}</pre>
      {/if}
    </div>
    <footer class="overlay-keys">
      <span><b>Esc</b> back</span>
    </footer>
  </div>
{/if}

{#if overlay.pendingWrite}
  <div
    class="modal-layer"
    data-confirm
    role="presentation"
  >
    <button
      type="button"
      class="modal-scrim"
      aria-label="Cancel"
      onclick={overlay.cancelConfirm}
    ></button>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" tabindex="-1">
      <h3 id="confirm-title">{overlay.pendingWrite.label}?</h3>
      <p class="hint">
        {#if overlay.pendingWrite.action === "accept"}
          Accepting risk records that you saw this and clears it from Needs you.
        {:else}
          This records your decision on this item.
        {/if}
        {overlay.pendingWrite.noteRequired ? "A note is required." : "A note is optional."}
        Esc cancels.
      </p>
      {#if overlay.pendingWrite.kind === "needs"}
        <label class="field-label" for="confirm-note">Note</label>
        <input
          id="confirm-note"
          class="field"
          type="text"
          data-confirm-note
          placeholder="What should the record say?"
          bind:value={overlay.confirmNote}
          onkeydown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void overlay.submitConfirm();
            }
          }}
        />
      {/if}
      {#if overlay.confirmLocalError}
        <p class="err" data-confirm-local-error>{overlay.confirmLocalError}</p>
      {/if}
      {#if overlay.writeError}
        <p class="err" data-write-error>{overlay.writeError}</p>
      {/if}
      <div class="row">
        <button type="button" class="btn" data-confirm-cancel onclick={overlay.cancelConfirm}>
          Cancel
        </button>
        <button
          type="button"
          class="btn primary"
          data-confirm-submit
          disabled={overlay.writeBusy ||
            (overlay.pendingWrite.noteRequired && overlay.confirmNote.trim().length === 0)}
          onclick={() => void overlay.submitConfirm()}
        >
          {overlay.pendingWrite.label}
        </button>
      </div>
    </div>
  </div>
{/if}
