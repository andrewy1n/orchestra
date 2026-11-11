<script lang="ts">
  import { hub } from "../state/hub.svelte";
  import HubPanel from "./HubPanel.svelte";
  import PhaseCard from "./PhaseCard.svelte";
  import WorkNext from "./WorkNext.svelte";

  const empty = $derived(
    hub.data !== null &&
      hub.data.work_next.length === 0 &&
      hub.data.needs_you.length === 0 &&
      hub.data.active_phases.length === 0 &&
      hub.data.open_ideas.length === 0,
  );
</script>

<section class="hub" data-hub>
  <header class="hub-head">
    <h1 class="hub-h1">Work</h1>
  </header>
  {#if hub.error}
    <p class="hub-status" data-hub-status role="alert">{hub.error}</p>
  {:else if !hub.data}
    <p class="hub-status" data-hub-status>Loading work…</p>
  {/if}
  {#if hub.data}
    {#if empty}
      <p class="hub-status" data-hub-empty>Nothing is open.</p>
    {:else}
      {#if hub.data.active_phases.length > 0}
        <section class="hub-active" data-active-phases>
          <h2 class="hub-section">Active phases <span class="hub-count">{hub.data.active_phases.length}</span></h2>
          {#each hub.data.active_phases as phase (phase.href)}
            <PhaseCard item={phase} />
          {/each}
        </section>
      {/if}
      <div class="hub-split" data-hub-row>
        <div class="hub-split-main">
          <h2 class="hub-section">Work next</h2>
          <WorkNext items={hub.data.work_next} />
        </div>
        {#if hub.data.needs_you.length > 0}
          <HubPanel name="needs-you" label="Needs you" items={hub.data.needs_you} />
        {/if}
      </div>
      {#if hub.data.open_ideas.length > 0}
        <div class="hub-panels">
          <HubPanel name="open-ideas" label="Open ideas" items={hub.data.open_ideas} grouped />
        </div>
      {/if}
    {/if}
  {/if}
</section>
