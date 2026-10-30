<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { phase } from "$lib/state/phase.svelte";
  import { openGraphTask, openRequirement } from "$lib/state/refs";
  import TaskGraphBoard from "../../TaskGraphBoard.svelte";
  import type { Theme } from "../../theme";
  import { chipVariant } from "./chipVariant";

  let { kind, theme }: { kind: string; theme: Theme } = $props();
</script>

{#if kind === "phase" && phase.phaseTabs.length}
  <Tabs.Root
    value={phase.activePhaseTab}
    onValueChange={(tab) => phase.selectPhaseTab(tab)}
  >
    <Tabs.List class="h-auto flex-wrap" data-phase-tabs>
      {#each phase.phaseTabs as tab (tab)}
        <Tabs.Trigger value={tab} data-phase-tab={tab}>{tab}</Tabs.Trigger>
      {/each}
    </Tabs.List>
  </Tabs.Root>
{/if}
{#if phase.phaseChrome}
  <div class="phase-chrome" data-phase-chrome>
    <div class="chips" data-detail-chips data-phase-chips>
      {#each phase.phaseChrome.chips as chip (chip.label)}
        <Badge variant={chipVariant(chip.tone)}>{chip.label}</Badge>
      {/each}
    </div>
    <p class="phase-next" data-phase-next title={phase.phaseChrome.nextAction}>
      <span class="phase-next-label">Next</span>
      {phase.phaseChrome.nextAction}
    </p>
    {#if phase.phaseChrome.requirements.length}
      <div class="phase-reqs" data-phase-reqs>
        {#each phase.phaseChrome.requirements as req (req.id)}
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
{#if phase.phaseTaskGraph?.show}
  <TaskGraphBoard
    graph={phase.phaseTaskGraph}
    onselect={(id) => openGraphTask(id)}
    colorMode={theme}
  />
{/if}
{#if phase.taskView}
  <div class="task-board" data-task-board data-detail-section="Tasks">
    {#if phase.taskView.length}
      <div class="task-rows">
        {#each phase.taskView as row (row.id)}
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
{#if phase.evidenceView}
  <div class="evidence-board" data-evidence-board>
    {#if phase.evidenceView.facts.length}
      <div class="chips" data-evidence-facts>
        {#each phase.evidenceView.facts as fact (fact.label)}
          <Badge variant="outline">
            <span class="fact-k">{fact.label}</span>
            {fact.value}
          </Badge>
        {/each}
      </div>
    {/if}
    {#if phase.evidenceView.rows.length}
      <div class="evidence-reqs" data-evidence-reqs>
        {#each phase.evidenceView.rows as row (row.id)}
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
    {:else if !phase.evidenceView.facts.length}
      <p class="empty-note">No evidence summary.</p>
    {/if}
  </div>
{/if}
