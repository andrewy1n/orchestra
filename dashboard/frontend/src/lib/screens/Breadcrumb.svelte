<script lang="ts">
  import { breadcrumbParts } from "$lib/state/areas";
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { navigation } from "$lib/state/route.svelte";

  const parts = $derived(
    breadcrumbParts(
      navigation.route,
      polling.snapshot,
      areas.items,
      polling.selectedEffort,
    ),
  );
</script>

<nav class="breadcrumb" data-breadcrumb aria-label="Breadcrumb">
  {#each parts as part, index (index)}
    {#if index > 0}<span class="crumb-sep" aria-hidden="true">{" › "}</span>{/if}
    {#if part.href}
      <a href={part.href}>{part.label}</a>
    {:else}
      <span aria-current="page">{part.label}</span>
    {/if}
  {/each}
</nav>
