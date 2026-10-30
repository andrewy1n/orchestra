<script lang="ts">
  import { journal } from "$lib/state/journal.svelte";
  import { openHash, recordHref } from "../../detail";
</script>

<section class="journal-screen" data-journal-screen>
  <header class="journal-bar">
    <button
      type="button"
      class="back"
      data-act="close-journal"
      onclick={() => openHash("")}
    >
      Back
    </button>
    <span class="journal-title">
      Journal{#if journal.effortName}
        {" "}· {journal.effortName}{/if}
    </span>
  </header>
  <input
    class="field"
    type="search"
    data-journal-filter
    aria-label="Filter journal"
    placeholder="Filter by subject or text"
    bind:value={journal.filter}
  />
  {#if journal.error}
    <p class="error-note">{journal.error}</p>
  {:else if !journal.data}
    <p class="empty-note">Loading journal…</p>
  {:else if journal.items.length === 0}
    <p class="empty-note">No journal entries</p>
  {:else}
    <div class="journal-list" data-journal-list>
      {#each journal.items as item (item.id)}
        <button
          type="button"
          class="lrow clickable"
          data-journal="{item.id}"
          data-record-type={item.record_type}
          onclick={() => openHash(recordHref(item.id))}
        >
          <span class="kind">{item.record_type}</span>
          <span class="text">{item.subject || item.text || ""}</span>
          {#if item.text && item.subject && item.text !== item.subject}
            <span class="meta">{item.text}</span>
          {/if}
        </button>
      {/each}
    </div>
  {/if}
</section>
