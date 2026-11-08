<script lang="ts">
  import type { HubItem } from "../../api-types";

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
  <h2 class="text-sm font-semibold">{label}</h2>
  {#if grouped}
    {#each groups as [effort, group] (effort)}
      <h3 class="meta">{effort}</h3>
      {#each group as item (item.href)}
        <a class="lrow clickable" href={item.href}>
          <span class="text"><strong>{item.title}</strong></span>
        </a>
      {/each}
    {/each}
  {:else}
    {#each items as item (item.href)}
      <a class="lrow clickable" href={item.href}>
        <span class="meta">{item.effort}</span>
        <span class="text">
          <strong>{item.title}</strong>{#if item.step}<span class="meta"> · {item.step}</span>{/if}
        </span>
      </a>
    {/each}
  {/if}
</section>
