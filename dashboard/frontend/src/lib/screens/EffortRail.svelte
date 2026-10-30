<script lang="ts">
  import { polling } from "$lib/state/polling.svelte";

  const effort = $derived(polling.effort);
</script>

<nav class="rail" aria-label="Efforts">
  <h2 class="rail-heading">Efforts</h2>
  {#if polling.loading}
    <p class="empty-note">Loading…</p>
  {:else if polling.error}
    <p class="error-note">{polling.error}</p>
  {:else}
    {#each polling.rail.shown as view (view.effort)}
      <button
        type="button"
        class="effort"
        class:on={effort?.effort === view.effort}
        class:finished={view.finished}
        data-effort={view.effort}
        onclick={() => polling.selectEffort(view.effort)}
      >
        <span
          class="dot"
          style:background={view.needs_you.length
            ? "var(--warn)"
            : view.finished
              ? "var(--faint)"
              : "var(--brand)"}
        ></span>
        <span>
          <span class="name">{view.effort}</span>
          <span class="sub" class:warn={view.needs_you.length > 0}>
            {view.kind}{#if view.finished} · finished{/if}{#if view.needs_you.length}
              · {view.needs_you.length} needs you{/if}
          </span>
        </span>
      </button>
    {/each}
    {#if polling.rail.hidden > 0 || polling.showFinished}
      <button
        type="button"
        class="show-finished"
        class:on={polling.showFinished}
        data-act="show-finished"
        aria-pressed={polling.showFinished}
        title="Show finished efforts"
        onclick={() => (polling.showFinished = !polling.showFinished)}
      >
        {polling.showFinished ? "Hide finished" : `${polling.rail.hidden} finished`}
      </button>
    {/if}
  {/if}
</nav>
