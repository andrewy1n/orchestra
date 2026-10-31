<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { phase } from "$lib/state/phase.svelte";
  import { md, openGraphTask, openRequirement } from "$lib/state/refs";
  import { cn } from "$lib/utils.js";
  import { openHash, taskHref } from "../../detail";
  import { STATUS_TABS } from "../../efforts";
  import TaskGraphBoard from "../../TaskGraphBoard.svelte";
  import type { Theme } from "../../theme";
  import type { StatusTab } from "../../types";
  import { chipVariant } from "./chipVariant";

  let { theme }: { theme: Theme } = $props();

  function reqTone(status: string): string {
    if (status === "pass" || status === "verified") {
      return "border-[color-mix(in_srgb,var(--done)_50%,var(--border))] dark:border-[color-mix(in_srgb,var(--done)_50%,var(--border))]";
    }
    if (status === "fail") {
      return "border-[color-mix(in_srgb,var(--fail)_50%,var(--border))] dark:border-[color-mix(in_srgb,var(--fail)_50%,var(--border))]";
    }
    return "";
  }

  function evidenceAccent(tone: string): string {
    if (tone === "ok") return "border-l-[var(--done)]";
    if (tone === "warn") return "border-l-[var(--warn)]";
    return "border-l-transparent";
  }

  function statusTone(status: string): string {
    const tones: Record<string, string> = {
      running: "text-[var(--running)]",
      ready: "text-[var(--ready)]",
      waiting: "text-[var(--waiting)]",
      done: "text-[var(--done)]",
    };
    return tones[status] ?? "";
  }

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

<div class="phase-page flex flex-col gap-4" data-phase-page data-detail="phase">
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
        <Tabs.List class="flex-wrap" data-phase-tabs>
          {#each phase.phaseTabs as tab (tab)}
            <Tabs.Trigger class="capitalize" value={tab} data-phase-tab={tab}>{tab}</Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>
    {/if}
    {#if phase.phaseChrome}
      <div class="flex flex-col gap-2 rounded-md border bg-muted p-3" data-phase-chrome>
        <div class="flex flex-wrap gap-x-2 gap-y-1" data-detail-chips data-phase-chips>
          {#each phase.phaseChrome.chips as chip (chip.label)}
            <Badge class="h-6" variant={chipVariant(chip.tone)}>{chip.label}</Badge>
          {/each}
        </div>
        <p class="truncate text-sm" data-phase-next title={phase.phaseChrome.nextAction}>
          <span class="mr-1.5 font-semibold">Next</span>
          {phase.phaseChrome.nextAction}
        </p>
        {#if phase.phaseChrome.requirements.length}
          <div class="flex flex-wrap gap-1.5" data-phase-reqs>
            {#each phase.phaseChrome.requirements as req (req.id)}
              <Button
                variant="outline"
                size="sm"
                class={cn("h-6", reqTone(req.status))}
                data-phase-req={req.id}
                title={req.text || req.id}
                onclick={() => openRequirement(req.id)}
              >
                <span class="font-semibold">{req.id}</span>
                <span class="font-normal text-muted-foreground">{req.status}</span>
              </Button>
            {/each}
          </div>
        {:else}
          <p class="text-xs text-muted-foreground" data-phase-reqs-empty>No requirements yet</p>
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
        value={phase.statusTab}
        onValueChange={(tab) => phase.chooseTab(tab as StatusTab)}
      >
        <Tabs.List variant="line" class="flex-wrap" data-status-tabs>
          {#each STATUS_TABS as tab (tab.name)}
            <Tabs.Trigger class="pointer-coarse:min-h-11" value={tab.name} data-tab={tab.name}>
              <b class="text-sm font-medium">{tab.label}</b>
              {#if phase.counts}
                <span class="text-xs tabular-nums">({phase.counts[tab.name]})</span>
              {/if}
            </Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>

      <div class="overflow-hidden rounded-md border">
        <Table.Root data-task-table>
          <Table.Header>
            <Table.Row class="bg-muted hover:bg-muted">
              <Table.Head class="w-[118px] text-muted-foreground">Status</Table.Head>
              <Table.Head class="text-muted-foreground">Task</Table.Head>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {#if phase.tasks.length === 0}
              <Table.Row class="hover:bg-transparent">
                <Table.Cell colspan={2} class="text-muted-foreground">No tasks in this tab.</Table.Cell>
              </Table.Row>
            {:else}
              {#each phase.tasks as task (task.id)}
                <!-- biome-ignore lint/a11y/useSemanticElements: a button element cannot be a table row -->
                <Table.Row
                  class="cursor-pointer focus-visible:bg-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
                  role="button"
                  tabindex={0}
                  data-task={task.id}
                  data-phase-of={task.phase}
                  onclick={() => openHash(taskHref(task.id))}
                  onkeydown={(event) => {
                    if (event.key === " ") event.preventDefault();
                    if (event.key === "Enter" || event.key === " ") openHash(taskHref(task.id));
                  }}
                >
                  <Table.Cell class={cn("font-semibold", statusTone(task.status))}>
                    {statusLabel(task.status)}
                  </Table.Cell>
                  <Table.Cell class="whitespace-normal text-pretty">{task.title || task.subject}</Table.Cell>
                </Table.Row>
              {/each}
            {/if}
          </Table.Body>
        </Table.Root>
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
          <div class="flex flex-wrap gap-x-2 gap-y-1" data-evidence-facts>
            {#each phase.evidenceView.facts as fact (fact.label)}
              <Badge variant="outline">
                <span class="fact-k">{fact.label}</span>
                {fact.value}
              </Badge>
            {/each}
          </div>
        {/if}
        {#if phase.evidenceView.rows.length}
          <div class="overflow-hidden rounded-md border">
            <Table.Root data-evidence-reqs>
              <Table.Header>
                <Table.Row class="bg-muted hover:bg-muted">
                  <Table.Head class="w-16 text-muted-foreground">Req</Table.Head>
                  <Table.Head class="w-28 text-muted-foreground">Status</Table.Head>
                  <Table.Head class="w-16 text-muted-foreground">Tasks</Table.Head>
                  <Table.Head class="text-muted-foreground">Summary</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each phase.evidenceView.rows as row (row.id)}
                  <!-- biome-ignore lint/a11y/useSemanticElements: a button element cannot be a table row -->
                  <Table.Row
                    class="cursor-pointer focus-visible:bg-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
                    role="button"
                    tabindex={0}
                    data-evidence-req={row.id}
                    onclick={() => openRequirement(row.id)}
                    onkeydown={(event) => {
                      if (event.key === " ") event.preventDefault();
                      if (event.key === "Enter" || event.key === " ") openRequirement(row.id);
                    }}
                  >
                    <Table.Cell class={cn("border-l-2 font-semibold", evidenceAccent(row.tone))}>
                      {row.id}
                    </Table.Cell>
                    <Table.Cell class="text-xs text-muted-foreground">{row.status}</Table.Cell>
                    <Table.Cell class="text-xs text-muted-foreground tabular-nums">{row.tasks}</Table.Cell>
                    <Table.Cell class="whitespace-normal">
                      <div class="flex flex-col gap-0.5">
                        <span class="text-pretty">{row.text}</span>
                        {#if row.next}
                          <span class="text-xs text-muted-foreground">next {row.next}</span>
                        {/if}
                      </div>
                    </Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if !phase.evidenceView.facts.length}
          <p class="empty-note">No evidence summary.</p>
        {/if}
      </div>
    {/if}
    {#each phase.view.sections as section, index (section.title + index)}
      <section class="flex max-w-[72ch] flex-col gap-2 text-sm">
        {#if section.title}
          <div class="font-semibold text-foreground" data-section-card>{section.title}</div>
        {/if}
        <div
          class="md rounded-md border bg-card px-3 py-2.5"
          data-detail-section={section.title || "body"}
        >{@html md(section.body, phase.linkCtx)}</div>
      </section>
    {/each}
    <pre data-detail-payload class="sr-only">{phase.view.probe}</pre>
  {/if}
</div>
