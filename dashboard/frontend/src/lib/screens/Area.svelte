<script lang="ts">
  import { areaRollup, startedIdeas } from "$lib/state/areas";
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { effortHref } from "../../detail";
  import { scanNeeds } from "../../detailView";
  import { renderMarkdown } from "../../markdown";
  import EffortRow from "./EffortRow.svelte";

  const area = $derived(areas.current);
  const open = $derived(area?.ideas.filter((idea) => idea.status === "open") ?? []);
  const started = $derived(area ? startedIdeas(area) : []);
  const efforts = $derived(
    (polling.snapshot?.efforts ?? []).filter((view) => view.area === area?.subject),
  );
  const rollup = $derived(area ? areaRollup(polling.snapshot?.efforts ?? [], area) : null);
  const needs = $derived(
    efforts.flatMap((view) =>
      view.needs_you.map((item) => ({ effort: view.effort, item, scan: scanNeeds(item) })),
    ),
  );
</script>

<section class="area-screen" data-area-screen>
  {#if areas.error}
    <p class="error-note">{areas.error}</p>
  {:else if !areas.loaded}
    <p class="empty-note">Loading area…</p>
  {:else if !area}
    <p class="empty-note">No area named {areas.subject}.</p>
  {:else}
    <h1 class="text-xl font-semibold" data-area-title>{area.title || area.subject}</h1>
    <div class="md" data-area-scope>{@html renderMarkdown(area.scope)}</div>

    {#if rollup}
      <p class="area-stats" data-area-stats>
        <span>{rollup.efforts} {rollup.efforts === 1 ? "effort" : "efforts"}</span>
        <span>{rollup.openIdeas} open {rollup.openIdeas === 1 ? "idea" : "ideas"}</span>
        <span>{rollup.needs} needs you</span>
      </p>
    {/if}

    <h2 class="ptitle">Needs you <span class="count">{needs.length}</span></h2>
    {#if needs.length === 0}
      <p class="empty-note">Nothing needs you.</p>
    {:else}
      <div class="area-needs" data-area-needs>
        {#each needs as row (`${row.effort}/${row.item.id}`)}
          <a
            class="lrow needs-row clickable"
            class:has-place={row.scan.place.length > 0}
            data-area-need={row.item.id}
            href={effortHref(row.effort)}
          >
            <span class="kind">{row.scan.kind}</span>
            {#if row.scan.place}<span class="where">{row.scan.place}</span>{/if}
            <span class="text">
              <span class="meta" data-need-effort>{row.effort}</span>
              {row.scan.claim}
            </span>
          </a>
        {/each}
      </div>
    {/if}

    <h2 class="ptitle">Efforts <span class="count">{efforts.length}</span></h2>
    {#if efforts.length === 0}
      <p class="empty-note">No efforts in this area.</p>
    {:else}
      <div class="area-efforts" data-area-efforts>
        {#each efforts as view (view.effort)}
          <EffortRow {view} />
        {/each}
      </div>
    {/if}

    <h2 class="ptitle">Ideas <span class="count">{open.length}</span></h2>
    {#if open.length === 0}
      <p class="empty-note">No open ideas.</p>
    {:else}
      <div class="area-ideas" data-area-open>
        {#each open as idea (idea.subject)}
          <div class="lrow" data-idea={idea.subject}>
            <span class="text">{idea.text || idea.subject}</span>
            <span class="meta">{idea.subject}</span>
          </div>
        {/each}
      </div>
    {/if}

    {#if started.length > 0}
      <div class="area-started" data-area-started>
        <h2 class="ptitle">Started as efforts <span class="count">{started.length}</span></h2>
        {#each started as idea (idea.subject)}
          <a
            class="lrow clickable"
            data-started-effort={idea.effort}
            href={effortHref(idea.effort)}
          >
            <span class="text">{idea.text || idea.subject}</span>
            <span class="meta">{idea.effort}</span>
          </a>
        {/each}
      </div>
    {/if}
  {/if}
</section>
