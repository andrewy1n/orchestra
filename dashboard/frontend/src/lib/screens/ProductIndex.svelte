<script lang="ts">
  import { groupByArea } from "$lib/state/areas";
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { effortHref } from "../../detail";
  import AreaCard from "./AreaCard.svelte";

  const grouped = $derived(
    groupByArea(polling.snapshot?.efforts ?? [], areas.items),
  );
</script>

<section class="product-index" data-product-index>
  <h1 class="text-xl font-semibold">Areas</h1>
  <div class="area-grid">
    {#each grouped.groups as group (group.area.subject)}
      <AreaCard area={group.area} efforts={group.efforts} />
    {/each}
  </div>

  {#if grouped.unplaced.length}
    <div class="unplaced" data-unplaced>
      <h2 class="ptitle">Not in an area</h2>
      {#each grouped.unplaced as view (view.effort)}
        <a class="lrow clickable" href={effortHref(view.effort)}>
          <span class="text">{view.effort}</span>
        </a>
      {/each}
    </div>
  {/if}
</section>
