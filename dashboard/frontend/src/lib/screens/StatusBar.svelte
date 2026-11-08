<script lang="ts">
  import { polling } from "$lib/state/polling.svelte";
</script>

{#if polling.pollError}
  <footer
    class="flex min-h-7 items-center gap-2 border-t border-[var(--line)] px-4 py-1.5 text-xs text-muted-foreground"
    role="alert"
  >
    <span class="size-2 shrink-0 rounded-full bg-[var(--fail)]" data-status-dot></span>
    <span data-status-text>{polling.pollError}</span>
  </footer>
{/if}
