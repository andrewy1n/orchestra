<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { overlay } from "$lib/state/overlay.svelte";
</script>

<Dialog.Root
  open={Boolean(overlay.pendingWrite)}
  onOpenChange={(open) => {
    if (!open) overlay.cancelConfirm();
  }}
>
  {#if overlay.pendingWrite}
    <Dialog.Content
      showCloseButton={false}
      data-confirm
      onOpenAutoFocus={(event) => event.preventDefault()}
      onCloseAutoFocus={(event) => event.preventDefault()}
    >
      <Dialog.Header>
        <Dialog.Title>{overlay.pendingWrite.label}?</Dialog.Title>
        <Dialog.Description>
          {#if overlay.pendingWrite.action === "accept"}
            Accepting risk records that you saw this and clears it from Needs you.
          {:else}
            This records your decision on this item.
          {/if}
          {overlay.pendingWrite.noteRequired ? "A note is required." : "A note is optional."}
          Esc cancels.
        </Dialog.Description>
      </Dialog.Header>
      {#if overlay.pendingWrite.kind === "needs"}
        <div class="grid gap-2">
          <label class="text-sm font-medium" for="confirm-note">Note</label>
          <Input
            id="confirm-note"
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
        </div>
      {/if}
      {#if overlay.confirmLocalError}
        <p class="text-sm text-destructive" data-confirm-local-error>{overlay.confirmLocalError}</p>
      {/if}
      {#if overlay.writeError}
        <p class="text-sm text-destructive" data-write-error>{overlay.writeError}</p>
      {/if}
      <Dialog.Footer>
        <Button type="button" variant="outline" data-confirm-cancel onclick={overlay.cancelConfirm}>
          Cancel
        </Button>
        <Button
          type="button"
          data-confirm-submit
          disabled={overlay.writeBusy ||
            (overlay.pendingWrite.noteRequired && overlay.confirmNote.trim().length === 0)}
          onclick={() => void overlay.submitConfirm()}
        >
          {overlay.pendingWrite.label}
        </Button>
      </Dialog.Footer>
    </Dialog.Content>
  {/if}
</Dialog.Root>
