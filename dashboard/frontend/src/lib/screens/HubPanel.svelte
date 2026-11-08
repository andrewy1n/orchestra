<script lang="ts">
  import type { HubItem } from "../../api-types";
  import { firstSentence } from "../../hubText";

  let {
    name,
    label,
    items,
    grouped = false,
  }: { name: string; label: string; items: HubItem[]; grouped?: boolean } = $props();

  const groups = $derived.by(() => {
    const byEffort = new Map<string, HubItem[]>();
    for (const item of items) {
      const list = byEffort.get(item.effort);
      if (list) list.push(item);
      else byEffort.set(item.effort, [item]);
    }
    return [...byEffort];
  });
</script>

<section class="hub-panel" data-panel={name}>
  <h2 class="hub-panel-head">{label} <span class="hub-count">{items.length}</span></h2>
  <div class="hub-panel-body">
    {#if grouped}
      {#each groups as [effort, group] (effort)}
        <h3 class="hub-group">{effort}</h3>
        {#each group as item (item.href)}
          <a class="hub-row hub-row-compact" href={item.href}>
            <span class="hub-title" title={item.title}>{firstSentence(item.title, 90)}</span>
          </a>
        {/each}
      {/each}
    {:else}
      {#each items as item (item.href)}
        <a class="hub-row hub-row-compact" href={item.href}>
          <span class="hub-main">
            <span class="hub-title" title={item.title}>{firstSentence(item.title, 90)}</span>
            <span class="hub-sub">{item.effort}{#if item.step}{" · "}{item.step}{/if}</span>
          </span>
        </a>
      {/each}
    {/if}
  </div>
</section>
