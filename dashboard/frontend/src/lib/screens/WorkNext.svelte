<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import type { HubItem } from "../../api-types";
  import { chipVariant } from "./chipVariant";

  let { items }: { items: HubItem[] } = $props();
</script>

<div class="work-next" data-work-next>
  {#each items as item (item.href)}
    <a class="lrow clickable" href={item.href}>
      <Badge variant={chipVariant(item.running ? "ok" : "accent")}>{item.kind}</Badge>
      <span class="meta">{item.effort}</span>
      <span class="text">
        <strong>{item.title}</strong>{#if item.step}<span class="meta"> · {item.step}</span>{/if}
      </span>
      <span class="meta" data-reason>{item.reason}</span>
    </a>
  {/each}
</div>
