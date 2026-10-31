<script lang="ts">
  import { journal } from "$lib/state/journal.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { backlogHref, journalHref, openHash } from "../../detail";
  import NeedsRows from "./NeedsRows.svelte";

  const effort = $derived(polling.effort);

  const panelClass =
    "mb-3 rounded-[var(--corner)] border border-[var(--line)] bg-[var(--panel)] px-3 pt-2.5 pb-2";
  const titleClass = "mb-1.5 flex items-baseline gap-2 text-sm font-semibold";
  const countClass = "font-medium tabular-nums text-muted-foreground";
  const emptyClass = "py-3.5 text-xs text-muted-foreground";
</script>

<aside class="side" aria-label="Details">
  {#if effort}
    {#if !polling.showNeedsInMain}
      <section
        class={[panelClass, effort.needs_you.length > 0 && "border-[var(--warn)]"]}
        data-side-needs
      >
        <h2
          class={[
            titleClass,
            effort.needs_you.length > 0
              ? "text-[var(--warn)]"
              : "text-[var(--ink)]",
          ]}
        >
          Needs you
          {#if effort.needs_you.length}
            <span class={countClass}>{effort.needs_you.length}</span>
          {/if}
        </h2>
        {#if effort.needs_you.length === 0}
          <p class={emptyClass}>Nothing needs you</p>
        {:else}
          <NeedsRows view={effort} />
        {/if}
      </section>
    {/if}

    {#if polling.showJournalTeaser}
      <section class={panelClass} data-side-journal-teaser>
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

    <section class={panelClass} data-side-backlog>
      <h2 class={[titleClass, "text-[var(--ink)]"]}>
        Backlog
        {#if polling.backlogItems.length}
          <span class={countClass}>{polling.backlogItems.length}</span>
        {/if}
      </h2>
      {#if polling.backlogItems.length === 0}
        <p class={emptyClass}>No backlog</p>
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
              <span
                class="truncate text-xs text-muted-foreground"
                data-record-id>{item.subject}</span
              >
            {/if}
          </button>
        {/each}
      {/if}
    </section>
  {/if}
</aside>
