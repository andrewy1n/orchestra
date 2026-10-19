<script lang="ts">
  import { onMount } from "svelte";
  import {
    defaultPhase,
    filteredTasks,
    resolvedPhase,
    STATUS_TABS,
    tabCounts,
    visibleEfforts,
  } from "./efforts";
  import { startTokenPoller } from "./poll";
  import { currentRoute, routeLabel, type Route } from "./router";
  import { applyTheme, DEFAULT_THEME, toggle, type Theme } from "./theme";
  import type { EffortView, Snapshot, StatusTab } from "./types";

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
  let showFinished = $state(false);

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

  const counts = $derived(effort ? tabCounts(effort, phaseSubject) : null);

  function selectEffort(name: string) {
    selectedEffort = name;
    pinnedPhase = null;
    statusTab = "active";
  }

  function selectPhase(target: string) {
    if (!effort) return;
    if (target === "all") {
      pinnedPhase = "all";
      return;
    }
    pinnedPhase = target === defaultPhase(effort) ? null : target;
  }

  function applySnapshot(data: Snapshot) {
    snapshot = data;
    loading = false;
    error = "";
    if (!selectedEffort) {
      const { shown } = visibleEfforts(data.efforts, showFinished);
      if (shown[0]) selectedEffort = shown[0].effort;
    }
  }

  onMount(() => {
    const sync = () => (route = currentRoute());
    window.addEventListener("hashchange", sync);

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
    };
  });
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">orchestra <span class="brand-sub">dashboard</span></div>
    <div class="crumbs" aria-live="polite">{routeLabel(route)}</div>
    <div class="top-actions">
      {#if rail.hidden > 0 || showFinished}
        <button
          type="button"
          class="ghost"
          class:on={showFinished}
          data-act="show-finished"
          aria-pressed={showFinished}
          title="Show finished efforts"
          onclick={() => (showFinished = !showFinished)}
        >
          {rail.hidden > 0 ? `+${rail.hidden} finished` : "finished"}
        </button>
      {/if}
      <button
        type="button"
        class="ghost"
        data-act="theme"
        aria-label="Theme"
        aria-pressed={theme === "dark"}
        title="Theme (t)"
        onclick={onToggleTheme}
      >
        ◐
      </button>
    </div>
  </header>

  <div class="layout">
    <nav class="rail" aria-label="Efforts">
      <p class="kicker">Efforts</p>
      {#if loading}
        <p class="empty-note">Loading…</p>
      {:else if error}
        <p class="empty-note">{error}</p>
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
                {view.kind}{#if view.needs_you.length}
                  · {view.needs_you.length} needs you{/if}
              </span>
            </span>
          </button>
        {/each}
      {/if}
    </nav>

    <main class="main" data-route={route.name}>
      {#if effort}
        <p class="goal" data-goal>{effort.goal}</p>

        {#if effort.phases.length}
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
                onclick={() => selectPhase(phase.subject)}
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

        <div class="tabs" data-status-tabs>
          {#each STATUS_TABS as tab}
            <button
              type="button"
              class="tab"
              class:on={statusTab === tab.name}
              data-tab={tab.name}
              onclick={() => (statusTab = tab.name)}
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
            <span>status</span>
            <span>task</span>
          </div>
          {#if tasks.length === 0}
            <p class="empty-note">No tasks in this tab</p>
          {:else}
            {#each tasks as task (task.id)}
              <div
                class="trow task"
                data-task={task.id}
                data-phase-of={task.phase}
              >
                <span class="st {task.status}">{task.status}</span>
                <span class="title">{task.title || task.subject}</span>
              </div>
            {/each}
          {/if}
        </div>
      {:else if !loading && !error}
        <p class="empty-note">No efforts in this store.</p>
      {/if}
    </main>

    <aside class="side" aria-label="Details"></aside>
  </div>

  <footer class="statusbar">
    {#if pollError}
      {pollError}
    {:else if snapshot}
      live
    {/if}
  </footer>
</div>
