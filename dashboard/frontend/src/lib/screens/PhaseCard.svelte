<script lang="ts">
  import type { HubItem } from "../../api-types";
  import { firstSentence, relativeTime } from "../../hubText";

  let { item }: { item: HubItem } = $props();

  const progress = $derived(item.progress);
  const tasks = $derived(progress?.tasks);
  const requirements = $derived(progress?.requirements);
  const provenPct = $derived(
    requirements && requirements.total > 0
      ? (requirements.proven / requirements.total) * 100
      : 0,
  );
</script>

{#if progress && tasks && requirements}
  <article class="phase-card" data-phase-card>
    <header class="pc-head" data-card-header>
      <a class="pc-title" href={item.href} title={item.title} data-title>{firstSentence(item.title)}</a>
      <span class="pc-chip" data-effort>{item.effort}</span>
      <span class="pc-chip" data-weight>{progress.weight}</span>
      <span class="pc-time">
        {#if item.running}<span class="pc-running" data-running>running</span>{" "}<span data-reason>{relativeTime(item.updated_at)}</span>{:else}<span data-reason>{item.reason}</span>{/if}
      </span>
    </header>

    <ol class="pc-stepper">
      {#each progress.stages as stage (stage.id)}
        <li
          class="pc-stage"
          data-stage={stage.id}
          data-state={stage.state}
          aria-current={stage.state === "current" ? "step" : undefined}
        >{stage.id}</li>
      {/each}
    </ol>

    <div class="pc-row" data-tasks>
      <span class="pc-name">Tasks</span>
      {#if tasks.total > 0}
        <span class="pc-bar" data-bar>
          {#each Array(tasks.done) as _, i (`d${i}`)}<span class="pc-seg" data-segment="done"></span>{/each}
          {#each Array(tasks.running) as _, i (`r${i}`)}<span class="pc-seg" data-segment="running"></span>{/each}
          {#each Array(tasks.remaining) as _, i (`m${i}`)}<span class="pc-seg" data-segment="remaining"></span>{/each}
        </span>
      {/if}
      <span class="pc-label" data-label>{tasks.label}</span>
    </div>

    <div class="pc-row" data-requirements>
      <span class="pc-name">Requirements</span>
      {#if requirements.total > 0}
        <span class="pc-bar" data-bar>
          <span class="pc-fill" style:width="{provenPct}%"></span>
        </span>
      {/if}
      <span class="pc-label">{requirements.label}</span>
    </div>

    {#if progress.repairs}
      <div class="pc-row pc-repairs" data-repairs>
        <span class="pc-name">Repairs</span>
        <span class="pc-label">{progress.repairs.label}</span>
      </div>
    {/if}

    <div class="pc-gate" data-gate>
      {#if progress.blockers.shown.length > 0}
        <span>Blocks close:</span>
        {#each progress.blockers.shown as blocker, i (blocker)}
          {#if i > 0}<span class="pc-sep" data-separator aria-hidden="true">·</span>{/if}
          <span class="pc-blocker" data-blocker>{blocker}</span>
        {/each}
        {#if progress.blockers.more > 0}
          <span data-more>+{progress.blockers.more} more</span>
        {/if}
      {:else}
        <span>Nothing blocks close</span>
      {/if}
    </div>
  </article>
{/if}
