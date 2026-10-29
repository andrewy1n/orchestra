<script lang="ts">
  import { overlay } from "$lib/state/overlay.svelte";
  import TaskGraphBoard from "../../TaskGraphBoard.svelte";
  import type { Theme } from "../../theme";

  let { kind, theme }: { kind: string; theme: Theme } = $props();
</script>

{#if kind === "phase" && overlay.phaseTabs.length}
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
