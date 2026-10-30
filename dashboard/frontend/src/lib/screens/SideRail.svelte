<script lang="ts">
  import { journal } from "$lib/state/journal.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { backlogHref, journalHref, openHash } from "../../detail";
  import NeedsRows from "./NeedsRows.svelte";

  const effort = $derived(polling.effort);
</script>

<aside class="side" aria-label="Details">
  {#if effort}
    {#if !polling.showNeedsInMain}
      <section
        class="panel"
        class:warn={effort.needs_you.length > 0}
        data-side-needs
      >
        <h2 class="ptitle">
          Needs you
          {#if effort.needs_you.length}
            <span class="count">{effort.needs_you.length}</span>
          {/if}
        </h2>
        {#if effort.needs_you.length === 0}
          <p class="empty-note">Nothing needs you</p>
        {:else}
          <NeedsRows view={effort} />
        {/if}
      </section>
    {/if}

    {#if polling.showJournalTeaser}
      <section class="panel" data-side-journal-teaser>
        <a
          class="lrow clickable"
          data-journal-teaser
          href={journalHref(effort.effort)}
          onclick={(e) => {
            e.preventDefault();
            openHash(journalHref(effort.effort));
          }}
        >
          <span class="kind accent">journal</span>
          <span class="text">
            Journal{#if journal.openCount !== null && journal.openCount > 0}
              {" "}{journal.openCount} open{/if}
          </span>
          {#if journal.error}
            <span class="meta">{journal.error}</span>
          {/if}
        </a>
      </section>
    {/if}

    <section class="panel" data-side-backlog>
      <h2 class="ptitle">
        Backlog
        {#if polling.backlogItems.length}
          <span class="count">{polling.backlogItems.length}</span>
        {/if}
      </h2>
      {#if polling.backlogItems.length === 0}
        <p class="empty-note">No backlog</p>
      {:else}
        {#each polling.backlogItems as item (item.id)}
          <button
            type="button"
            class="lrow clickable"
            data-backlog={item.id}
            onclick={() => openHash(backlogHref(effort.effort, item.id))}
          >
            <span class="text">{item.text || item.subject}</span>
            {#if item.subject && item.subject !== item.text}
              <span class="meta">{item.subject}</span>
            {/if}
          </button>
        {/each}
      {/if}
    </section>
  {/if}
</aside>
