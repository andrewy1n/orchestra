<script lang="ts">
  import { overlay } from "$lib/state/overlay.svelte";
</script>

{#if overlay.pendingWrite}
  <div
    class="modal-layer"
    data-confirm
    role="presentation"
  >
    <button
      type="button"
      class="modal-scrim"
      aria-label="Cancel"
      onclick={overlay.cancelConfirm}
    ></button>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" tabindex="-1">
      <h3 id="confirm-title">{overlay.pendingWrite.label}?</h3>
      <p class="hint">
        {#if overlay.pendingWrite.action === "accept"}
          Accepting risk records that you saw this and clears it from Needs you.
        {:else}
          This records your decision on this item.
        {/if}
        {overlay.pendingWrite.noteRequired ? "A note is required." : "A note is optional."}
        Esc cancels.
      </p>
      {#if overlay.pendingWrite.kind === "needs"}
        <label class="field-label" for="confirm-note">Note</label>
        <input
          id="confirm-note"
          class="field"
          type="text"
          data-confirm-note
          placeholder="What should the record say?"
          bind:value={overlay.confirmNote}
          onkeydown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void overlay.submitConfirm();
            }
          }}
        />
      {/if}
      {#if overlay.confirmLocalError}
        <p class="err" data-confirm-local-error>{overlay.confirmLocalError}</p>
      {/if}
      {#if overlay.writeError}
        <p class="err" data-write-error>{overlay.writeError}</p>
      {/if}
      <div class="row">
        <button type="button" class="btn" data-confirm-cancel onclick={overlay.cancelConfirm}>
          Cancel
        </button>
        <button
          type="button"
          class="btn primary"
          data-confirm-submit
          disabled={overlay.writeBusy ||
            (overlay.pendingWrite.noteRequired && overlay.confirmNote.trim().length === 0)}
          onclick={() => void overlay.submitConfirm()}
        >
          {overlay.pendingWrite.label}
        </button>
      </div>
    </div>
  </div>
{/if}
