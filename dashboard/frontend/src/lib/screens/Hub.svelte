<script lang="ts">
  import { hub } from "../state/hub.svelte";
  import HubPanel from "./HubPanel.svelte";
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
  <h1 class="text-xl font-semibold">Work</h1>
  {#if hub.data}
    <WorkNext items={hub.data.work_next} />
    {#if empty}
      <p class="meta" data-hub-empty>Nothing is open.</p>
    {:else}
      <div class="hub-panels">
        {#if hub.data.needs_you.length > 0}
          <HubPanel name="needs-you" label="Needs you" items={hub.data.needs_you} />
        {/if}
        {#if hub.data.active_phases.length > 0}
          <HubPanel name="active-phases" label="Active phases" items={hub.data.active_phases} />
        {/if}
        {#if hub.data.open_ideas.length > 0}
          <HubPanel name="open-ideas" label="Open ideas" items={hub.data.open_ideas} grouped />
        {/if}
      </div>
    {/if}
  {/if}
  <a href="#/areas">Areas</a>
</section>
