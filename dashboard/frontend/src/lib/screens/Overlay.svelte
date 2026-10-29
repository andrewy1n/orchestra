<script lang="ts">
  import { overlay } from "$lib/state/overlay.svelte";
  import { closeDetail } from "../../detail";
  import type { Theme } from "../../theme";
  import PhaseOverlay from "./PhaseOverlay.svelte";

  let { theme }: { theme: Theme } = $props();
  const target = $derived(overlay.target);
</script>

{#if target}
  <div
    class="overlay"
    data-detail={target.kind}
    role="dialog"
    aria-modal="true"
    aria-labelledby="overlay-who"
    tabindex="-1"
    inert={overlay.pendingWrite ? true : undefined}
  >
    <header class="overlay-bar">
      <button type="button" class="back" data-act="close-detail" onclick={closeDetail}>
        Back
      </button>
      <div class="overlay-title">
        <span class="who" id="overlay-who">{overlay.overlayView?.who ?? target.kind}</span>
        {#if overlay.overlayView?.ctx}
          <span class="ctx">{overlay.overlayView.ctx}</span>
        {/if}
      </div>
    </header>
    <div class="overlay-body">
      {#if overlay.detailLoading}
        <p class="empty-note">Loading…</p>
      {:else if overlay.detailError}
        <p class="error-note">{overlay.detailError}</p>
      {:else if overlay.detailPayload && overlay.overlayView}
        <PhaseOverlay kind={target.kind} {theme} />
        {#if !overlay.phaseChrome && overlay.overlayView.chips.length}
          <div class="chips" data-detail-chips>
            {#each overlay.overlayView.chips as chip (chip.label)}
              <span class="chip {chip.tone || ''}">{chip.label}</span>
            {/each}
          </div>
        {/if}
        {#if overlay.writeError && !overlay.pendingWrite}
          <p class="write-error" data-write-error>{overlay.writeError}</p>
        {/if}
        {#each overlay.overlayView.sections as section, index (section.title + index)}
          {#if section.title}
            <div class="section-title" data-section-card>{section.title}</div>
          {/if}
          <div
            class="md section-card"
            data-detail-section={section.title || "body"}
          >{@html overlay.md(section.body)}</div>
        {/each}
        {#if overlay.overlayChoices.length}
          <div class="overlay-actions" data-write-actions>
            {#each overlay.overlayChoices as choice (choice.action)}
              <button
                type="button"
                class="btn"
                class:primary={choice.action === "accept"}
                data-write-action={choice.action}
                onclick={() => overlay.openConfirm(choice)}
              >
                {choice.label}
              </button>
            {/each}
          </div>
        {/if}
        <!-- Probe text for acceptances; not shown as a JSON dump. -->
        <pre data-detail-payload class="sr-only">{overlay.overlayView.probe}</pre>
      {/if}
    </div>
    <footer class="overlay-keys">
      <span><b>Esc</b> back</span>
    </footer>
  </div>
{/if}
