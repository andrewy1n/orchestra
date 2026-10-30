<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import { overlay } from "$lib/state/overlay.svelte";
  import { closeDetail } from "../../detail";
  import type { Theme } from "../../theme";
  import { chipVariant } from "./chipVariant";
  import PhaseOverlay from "./PhaseOverlay.svelte";

  let { theme }: { theme: Theme } = $props();
  const target = $derived(overlay.target);
</script>

<Dialog.Root
  open={Boolean(target)}
  onOpenChange={(open) => {
    if (!open) closeDetail();
  }}
>
  {#if target}
    <Dialog.Content
      showCloseButton={false}
      class="flex h-[calc(100dvh-2rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-5xl"
      data-detail={target.kind}
      aria-describedby={undefined}
      inert={overlay.pendingWrite ? true : undefined}
      onOpenAutoFocus={(event) => event.preventDefault()}
      onCloseAutoFocus={(event) => event.preventDefault()}
    >
      <header class="flex items-center gap-3 border-b px-4 py-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          data-act="close-detail"
          onclick={closeDetail}
        >
          Back
        </Button>
        <div class="flex min-w-0 flex-col">
          <Dialog.Title class="truncate text-base font-semibold" id="overlay-who">
            {overlay.overlayView?.who ?? target.kind}
          </Dialog.Title>
          {#if overlay.overlayView?.ctx}
            <span class="truncate text-xs text-muted-foreground">{overlay.overlayView.ctx}</span>
          {/if}
        </div>
      </header>
      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {#if overlay.detailLoading}
          <p class="empty-note">Loading…</p>
        {:else if overlay.detailError}
          <p class="error-note">{overlay.detailError}</p>
        {:else if overlay.detailPayload && overlay.overlayView}
          <PhaseOverlay kind={target.kind} {theme} />
          {#if !overlay.phaseChrome && overlay.overlayView.chips.length}
            <div class="chips" data-detail-chips>
              {#each overlay.overlayView.chips as chip (chip.label)}
                <Badge variant={chipVariant(chip.tone)}>{chip.label}</Badge>
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
                <Button
                  type="button"
                  variant={choice.action === "accept" ? "default" : "outline"}
                  data-write-action={choice.action}
                  onclick={() => overlay.openConfirm(choice)}
                >
                  {choice.label}
                </Button>
              {/each}
            </div>
          {/if}
          <!-- Probe text for acceptances; not shown as a JSON dump. -->
          <pre data-detail-payload class="sr-only">{overlay.overlayView.probe}</pre>
        {/if}
      </div>
      <footer class="border-t px-4 py-2 text-xs text-muted-foreground">
        <span><b>Esc</b> back</span>
      </footer>
    </Dialog.Content>
  {/if}
</Dialog.Root>
