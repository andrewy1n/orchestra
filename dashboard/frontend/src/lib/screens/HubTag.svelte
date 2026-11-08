<script lang="ts">
  let { kind, running = false }: { kind: string; running?: boolean } = $props();

  const tone = $derived(running ? "running" : kind);
  const label = $derived(
    running ? "Running" : kind === "needs" ? "Needs you" : kind === "idea" ? "Idea" : "Phase",
  );
</script>

<span class="hub-tag" data-tone={tone}>{label}</span>
