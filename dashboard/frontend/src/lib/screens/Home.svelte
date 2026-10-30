<script lang="ts">
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { areaHref, openHash, taskHref } from "../../detail";
  import { STATUS_TABS } from "../../efforts";
  import type { EffortView } from "../../types";
  import NeedsRows from "./NeedsRows.svelte";

  let { effort }: { effort: EffortView } = $props();
  const hasMilestones = $derived(polling.hasMilestones);
  const owner = $derived(
    effort.area ? areas.items.find((item) => item.subject === effort.area) : undefined,
  );

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
</script>

<header class="effort-head">
  <h1 class="effort-title" data-effort-title>{effort.effort}</h1>
  {#if owner}
    <a class="area-chip" data-area-chip href={areaHref(owner.subject)}>{owner.title}</a>
  {/if}
  <p class="goal" data-goal>{effort.goal}</p>
</header>

{#if polling.showNeedsInMain}
  <section class="needs-block" data-side-needs>
    <h2 class="ptitle">
      Needs you <span class="count">{effort.needs_you.length}</span>
    </h2>
    <NeedsRows view={effort} />
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
