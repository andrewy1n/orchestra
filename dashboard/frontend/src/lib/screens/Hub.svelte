<script lang="ts">
  import { hub } from "../state/hub.svelte";
  import WorkNext from "./WorkNext.svelte";
</script>

<section class="hub" data-hub>
  <h1 class="text-xl font-semibold">Work</h1>
  {#if hub.data}
    <WorkNext items={hub.data.work_next} />
  {/if}
  <a href="#/areas">Areas</a>
</section>
