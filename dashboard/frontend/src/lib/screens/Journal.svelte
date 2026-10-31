<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { journal } from "$lib/state/journal.svelte";
  import { leaveHref } from "$lib/state/polling.svelte";
  import { openHash, recordHref } from "../../detail";
</script>

<section class="journal-screen" data-journal-screen>
  <header class="flex items-center gap-2.5">
    <Button
      variant="ghost"
      size="sm"
      data-act="close-journal"
      onclick={() => openHash(leaveHref())}
    >
      Back
    </Button>
    <h1 class="text-xl font-semibold text-foreground">
      Journal{#if journal.effortName}
        {" "}· {journal.effortName}{/if}
    </h1>
  </header>
  <Input
    class="max-w-sm"
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
