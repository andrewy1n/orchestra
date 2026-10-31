<script lang="ts">
  import { polling } from "$lib/state/polling.svelte";
</script>

<footer
  class="flex min-h-7 items-center gap-2 border-t border-[var(--line)] px-4 py-1.5 text-xs text-muted-foreground"
>
  {#if polling.pollError || polling.snapshot}
    <span
      class={[
        "size-2 shrink-0 rounded-full",
        polling.pollError ? "bg-[var(--fail)]" : "bg-[var(--done)]",
      ]}
      data-status-dot
    ></span>
    <span data-status-text>{polling.pollError || "Live"}</span>
  {/if}
</footer>
