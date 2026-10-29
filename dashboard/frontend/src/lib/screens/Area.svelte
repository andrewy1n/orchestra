<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
  } from "$lib/components/ui/collapsible";
  import { areas } from "$lib/state/areas.svelte";
  import { polling } from "$lib/state/polling.svelte";
  import { openHash, phaseHref } from "../../detail";
  import { renderMarkdown } from "../../markdown";

  const area = $derived(areas.current);
  const open = $derived(area?.ideas.filter((idea) => idea.status === "open") ?? []);
  const moved = $derived(area?.ideas.filter((idea) => idea.status !== "open") ?? []);

  function showEffort(event: MouseEvent, effort: string) {
    event.preventDefault();
    polling.selectEffort(effort);
    openHash("");
  }
</script>

<section class="area-screen" data-area-screen>
  <header class="journal-bar">
    <Button variant="ghost" size="sm" data-act="close-area" onclick={() => openHash("")}>
      Back
    </Button>
    <span class="journal-title">{area?.title ?? areas.subject}</span>
  </header>

  {#if areas.error}
    <p class="error-note">{areas.error}</p>
  {:else if !areas.loaded}
    <p class="empty-note">Loading area…</p>
  {:else if !area}
    <p class="empty-note">No area named {areas.subject}.</p>
  {:else}
    <div class="md" data-area-scope>{@html renderMarkdown(area.scope)}</div>

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

    {#if moved.length}
      <Collapsible class="area-moved" data-area-moved>
        <CollapsibleTrigger class="area-moved-trigger" data-area-moved-toggle>
          Moved to effort <Badge variant="secondary">{moved.length}</Badge>
        </CollapsibleTrigger>
        <CollapsibleContent>
          {#each moved as idea (idea.subject)}
            <div class="lrow" data-idea={idea.subject}>
              <span class="text">{idea.text || idea.subject}</span>
              {#if idea.effort && idea.phase}
                <a class="meta" href={phaseHref(idea.effort, idea.phase)} data-idea-link="phase">
                  {idea.effort} / {idea.phase}
                </a>
              {:else if idea.effort}
                <a
                  class="meta"
                  href="#/"
                  data-idea-link="effort"
                  onclick={(event) => showEffort(event, idea.effort)}
                >
                  {idea.effort}
                </a>
              {/if}
            </div>
          {/each}
        </CollapsibleContent>
      </Collapsible>
    {/if}
  {/if}
</section>
