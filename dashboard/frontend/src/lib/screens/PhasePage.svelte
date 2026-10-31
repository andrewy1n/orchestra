<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { phase } from "$lib/state/phase.svelte";
  import { md, openGraphTask, openRequirement } from "$lib/state/refs";
  import { openHash, taskHref } from "../../detail";
  import { STATUS_TABS } from "../../efforts";
  import TaskGraphBoard from "../../TaskGraphBoard.svelte";
  import type { Theme } from "../../theme";
  import type { StatusTab } from "../../types";
  import { chipVariant } from "./chipVariant";

  let { theme }: { theme: Theme } = $props();

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
</script>

<div class="phase-page" data-phase-page data-detail="phase">
  {#if phase.loading}
    <p class="empty-note">Loading…</p>
  {:else if phase.error}
    <p class="error-note">{phase.error}</p>
  {:else if phase.payload && phase.view}
    <header class="phase-head">
      <h1 class="phase-title" data-phase-title>{phase.view.who}</h1>
      <span class="phase-state" data-phase-state>{phase.state}</span>
    </header>
    {#if phase.phaseTabs.length}
      <Tabs.Root
        value={phase.activePhaseTab}
        onValueChange={(tab) => phase.selectPhaseTab(tab)}
      >
        <Tabs.List class="h-auto flex-wrap" data-phase-tabs>
          {#each phase.phaseTabs as tab (tab)}
            <Tabs.Trigger class="capitalize" value={tab} data-phase-tab={tab}>{tab}</Tabs.Trigger>
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
    {#if phase.activePhaseTab === "overview" && phase.routeEffort}
      <Tabs.Root
        class="mt-3 mb-2.5"
        value={phase.statusTab}
        onValueChange={(tab) => phase.chooseTab(tab as StatusTab)}
      >
        <Tabs.List variant="line" class="h-auto flex-wrap" data-status-tabs>
          {#each STATUS_TABS as tab (tab.name)}
            <Tabs.Trigger value={tab.name} data-tab={tab.name}>
              <b class="text-sm font-medium">{tab.label}</b>
              {#if phase.counts}
                <span class="text-xs tabular-nums">({phase.counts[tab.name]})</span>
              {/if}
            </Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>

      <div class="table" data-task-table style="--cols: 118px 1fr">
        <div class="trow thead">
          <span>Status</span>
          <span>Task</span>
        </div>
        {#if phase.tasks.length === 0}
          <p class="empty-note">No tasks in this tab.</p>
        {:else}
          {#each phase.tasks as task (task.id)}
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
    {#each phase.view.sections as section, index (section.title + index)}
      {#if section.title}
        <div class="section-title" data-section-card>{section.title}</div>
      {/if}
      <div
        class="md section-card"
        data-detail-section={section.title || "body"}
      >{@html md(section.body, phase.linkCtx)}</div>
    {/each}
    <pre data-detail-payload class="sr-only">{phase.view.probe}</pre>
  {/if}
</div>
