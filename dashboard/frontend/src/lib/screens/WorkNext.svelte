<script lang="ts">
  import type { HubItem } from "../../api-types";
  import { firstSentence } from "../../hubText";
  import HubTag from "./HubTag.svelte";

  let { items }: { items: HubItem[] } = $props();
</script>

<div class="work-next" data-work-next>
  {#each items as item (item.href)}
    <a class="hub-row" href={item.href}>
      <HubTag kind={item.kind} running={item.running} />
      <span class="hub-main">
        <span class="hub-title" title={item.title}>{firstSentence(item.title)}</span>
        <span class="hub-sub">{item.effort}{#if item.step}{" · "}{item.step}{/if}</span>
      </span>
      <span class="hub-reason" data-reason>{item.reason}</span>
    </a>
  {/each}
</div>
