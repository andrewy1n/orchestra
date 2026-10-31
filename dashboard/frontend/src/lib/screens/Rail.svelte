<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { railItems, routePhase } from "$lib/state/areas";
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { navigation } from "$lib/state/route.svelte";

  const rail = $derived(
    railItems(
      navigation.route,
      polling.snapshot,
      areas.items,
      polling.selectedEffort,
    ),
  );
  const currentView = $derived(
    polling.snapshot?.efforts.find(
      (view) => view.effort === rail.items.find((item) => item.current)?.key,
    ),
  );
  const phaseEffort = $derived(
    routePhase(navigation.route, polling.snapshot?.efforts ?? [])?.effort.effort,
  );
  let showDonePhases = $state(false);
  const heading = $derived(
    rail.level === "area"
      ? "Areas"
      : rail.level === "phase"
        ? (phaseEffort ?? "Phases")
        : (areas.items.find((area) => area.subject === currentView?.area)?.title ??
          "Efforts"),
  );
  const kinds = $derived(
    new Map((polling.snapshot?.efforts ?? []).map((view) => [view.effort, view.kind])),
  );
  const hiddenKeys = $derived(
    new Set(
      rail.level === "effort" && !polling.showFinished
        ? rail.items
            .filter((item) => item.finished && item.needs === 0 && !item.current)
            .map((item) => item.key)
        : rail.level === "phase" && !showDonePhases
          ? rail.items
              .filter((item) => item.finished && !item.current)
              .map((item) => item.key)
          : [],
    ),
  );
  const shown = $derived(rail.items.filter((item) => !hiddenKeys.has(item.key)));
</script>

{#if rail.level !== "product"}
  <nav class="rail" data-rail-level={rail.level} aria-label={heading}>
    <h2 class="rail-heading">{heading}</h2>
    {#if polling.loading}
      <p class="empty-note">Loading…</p>
    {:else if polling.error}
      <p class="error-note">{polling.error}</p>
    {:else}
      {#each shown as item (item.key)}
        <a
          class={[
            "grid w-full grid-cols-[14px_1fr] items-baseline gap-2 rounded-md border border-transparent px-2 py-[7px] text-sm no-underline hover:bg-muted pointer-coarse:min-h-11",
            item.current &&
              "border-border bg-muted shadow-[inset_2px_0_0_var(--brand)]",
            item.finished && "text-muted-foreground",
          ]}
          data-rail-item={item.key}
          href={item.href}
          aria-current={item.current ? "page" : undefined}
        >
          <span
            class={[
              "mt-1 size-2 rounded-full",
              item.needs
                ? "bg-[var(--warn)]"
                : item.finished
                  ? "bg-[var(--faint)]"
                  : "bg-[var(--brand)]",
            ]}
          ></span>
          <span>
            <span class={["name block text-sm", item.current ? "font-semibold" : "font-medium"]}>
              {item.label}
            </span>
            {#if rail.level === "effort"}
              <span
                class={[
                  "block text-xs leading-snug",
                  item.needs > 0 ? "text-[var(--warn)]" : "text-muted-foreground",
                ]}
              >
                {kinds.get(item.key)}{#if item.finished} · finished{/if}{#if item.needs}
                  · {item.needs} needs you{/if}
              </span>
            {:else if item.needs > 0}
              <span class="block text-xs leading-snug text-[var(--warn)]">
                {item.needs} needs you
              </span>
            {/if}
          </span>
        </a>
      {/each}
      {#if rail.level === "effort" && (hiddenKeys.size > 0 || polling.showFinished)}
        <Button
          variant="outline"
          size="xs"
          class="mt-2.5 w-full justify-start aria-pressed:bg-muted pointer-coarse:min-h-11"
          data-act="show-finished"
          aria-pressed={polling.showFinished}
          title="Show finished efforts"
          onclick={() => (polling.showFinished = !polling.showFinished)}
        >
          {polling.showFinished ? "Hide finished" : `${hiddenKeys.size} finished`}
        </Button>
      {/if}
      {#if rail.level === "phase" && (hiddenKeys.size > 0 || showDonePhases)}
        <Button
          variant="outline"
          size="xs"
          class="mt-2.5 w-full justify-start aria-pressed:bg-muted pointer-coarse:min-h-11"
          data-act="show-done-phases"
          aria-pressed={showDonePhases}
          title="Show done phases"
          onclick={() => (showDonePhases = !showDonePhases)}
        >
          {showDonePhases ? "Hide done" : `Show ${hiddenKeys.size} done`}
        </Button>
      {/if}
    {/if}
  </nav>
{/if}
