<script lang="ts">
  import { product } from "$lib/state/product.svelte";
  import type { ProductEntry } from "../../api-types";
</script>

{#snippet entries(title: string, key: string, items: ProductEntry[])}
  <div data-product-section={key}>
    <h2 class="ptitle">{title}</h2>
    {#if items.length === 0}
      <p class="empty-note" data-product-empty={key}>None recorded.</p>
    {:else}
      <ul>
        {#each items as item (item.subject)}
          <li data-product-item={item.subject}>
            <span class="font-semibold" data-item-title>{item.title}</span>
            <span class="chip" data-item-status>{item.status}</span>
            <p data-item-description>{item.description}</p>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
{/snippet}

{#if product.error}
  <section class="product-overview" data-product-overview>
    <p class="empty-note" role="alert" data-product-error>{product.error}</p>
  </section>
{:else if product.overview}
  <section class="product-overview" data-product-overview>
    {#if product.overview.statement}
      <div data-product-statement>
        <p data-statement-purpose>{product.overview.statement.purpose}</p>
        <p data-statement-audience>{product.overview.statement.audience}</p>
      </div>
    {:else}
      <p class="empty-note" data-product-no-statement>No product statement recorded.</p>
    {/if}
    {@render entries("Capabilities", "capabilities", product.overview.capabilities)}
    {@render entries("Goals", "goals", product.overview.goals)}
  </section>
{/if}
