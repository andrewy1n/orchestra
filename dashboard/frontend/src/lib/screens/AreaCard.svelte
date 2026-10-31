<script lang="ts">
  import { areaRollup, firstSentence } from "$lib/state/areas";
  import type { AreaView } from "../../api-types";
  import { areaHref } from "../../detail";
  import type { EffortView } from "../../types";

  let { area, efforts }: { area: AreaView; efforts: EffortView[] } = $props();
  const rollup = $derived(areaRollup(efforts, area));
</script>

<a class="area-card" data-area-card={area.subject} href={areaHref(area.subject)}>
  <h2 class="area-card-title" data-card-title>{area.title || area.subject}</h2>
  <p class="area-card-scope" data-card-scope>{firstSentence(area.scope)}</p>
  <p class="area-card-counts">
    <span data-card-efforts
      >{rollup.efforts} {rollup.efforts === 1 ? "effort" : "efforts"}</span
    >
    <span data-card-ideas
      >{rollup.openIdeas} open {rollup.openIdeas === 1 ? "idea" : "ideas"}</span
    >
  </p>
  {#if efforts.length}
    <ul class="area-card-efforts">
      {#each efforts as view (view.effort)}
        <li data-card-effort>{view.effort}</li>
      {/each}
    </ul>
  {/if}
</a>
