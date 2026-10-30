<script lang="ts">
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { areaHref, phaseHref } from "../../detail";
  import type { EffortView, PhaseRow } from "../../types";
  import NeedsRows from "./NeedsRows.svelte";

  let { effort }: { effort: EffortView } = $props();
  const hasMilestones = $derived(polling.hasMilestones);
  const owner = $derived(
    effort.area ? areas.items.find((item) => item.subject === effort.area) : undefined,
  );

  function percent(phase: PhaseRow): number {
    return phase.total > 0 ? Math.round((phase.done / phase.total) * 100) : 0;
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

{#snippet phaseRow(phase: PhaseRow)}
  <a
    class="phase-row"
    class:done={phase.state === "done"}
    class:live={phase.state === "in_progress"}
    data-phase={phase.subject}
    data-phase-row={phase.subject}
    href={phaseHref(effort.effort, phase.subject)}
  >
    <span class="name">{phase.title || phase.subject}</span>
    <span class="cnt">{phase.done}/{phase.total}</span>
    <span
      class="bar"
      role="progressbar"
      aria-label="{phase.title || phase.subject} progress"
      aria-valuemin="0"
      aria-valuemax="100"
      aria-valuenow={percent(phase)}
    >
      <span class="bar-fill" style="width: {percent(phase)}%"></span>
    </span>
  </a>
{/snippet}

{#if effort.phases.length}
  {#if hasMilestones}
    <section class="phases-block" data-phases-block>
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
                {@render phaseRow(phase)}
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </section>
  {:else}
    <section class="phases-block" data-phases-list>
      {#each effort.phases
        .slice()
        .sort((a, b) => a.ordinal - b.ordinal) as phase (phase.subject)}
        {@render phaseRow(phase)}
      {/each}
    </section>
  {/if}
{/if}
