<script lang="ts">
  import { overlay } from "$lib/state/overlay.svelte";
  import { linkify } from "$lib/state/refs";
  import { needsHref, openHash } from "../../detail";
  import { scanNeeds } from "../../detailView";
  import type { EffortView } from "../../types";

  let { view }: { view: EffortView } = $props();
</script>

{#each view.needs_you as item (item.id)}
  {@const scan = scanNeeds(item)}
  <button
    type="button"
    class="lrow needs-row clickable"
    class:has-place={scan.place.length > 0}
    data-needs={item.id}
    onclick={(e) => {
      const anchor = (e.target as HTMLElement | null)?.closest?.("a[href]");
      if (anchor) {
        e.preventDefault();
        e.stopPropagation();
        openHash(anchor.getAttribute("href") || "");
        return;
      }
      openHash(needsHref(view.effort, item.id));
    }}
  >
    <span class="kind">{scan.kind}</span>
    {#if scan.place}<span class="where text-xs" data-record-id>{scan.place}</span>{/if}
    <span class="text">{@html linkify(scan.claim, overlay.linkCtx)}</span>
  </button>
{/each}
