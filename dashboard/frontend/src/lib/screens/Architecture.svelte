<script lang="ts">
  import { architecture, bindArchitecture } from "$lib/state/architecture.svelte";
  import type {
    ArchitectureConstraint,
    ArchitectureDecision,
  } from "../../api-types";

  bindArchitecture();
</script>

{#snippet notes(
  decisions: ArchitectureDecision[],
  constraints: ArchitectureConstraint[],
)}
  {#each decisions as decision (decision.title)}
    <p data-architecture-decision={decision.title}>
      <span class="font-semibold">{decision.title}</span>
      {#if decision.status === "proposed"}<span class="chip">proposed</span>{/if}
      {decision.rationale}
    </p>
  {/each}
  {#each constraints as constraint (constraint.name)}
    <p data-architecture-constraint={constraint.name}>
      <span class="font-semibold">{constraint.name}</span>
      {constraint.rule}
      <span class="chip" data-constraint-outcome>{constraint.outcome}</span>
    </p>
  {/each}
{/snippet}

<section class="architecture" data-architecture>
  <h1 class="text-xl font-semibold">Architecture</h1>
  {#if architecture.error}
    <p class="empty-note" role="alert" data-architecture-error>{architecture.error}</p>
  {:else if architecture.view}
    {#if architecture.view.areas.length === 0}
      <p class="empty-note" data-architecture-empty>No component exists.</p>
    {/if}
    {#each architecture.view.areas as area (area.name)}
      <div data-architecture-area={area.name}>
        <h2 class="ptitle">
          <a href={`#/architecture/area/${encodeURIComponent(area.name)}`}>{area.name}</a>
        </h2>
        {#each area.components as component (component.name)}
          <div data-architecture-component={component.name}>
            <h3 class="font-semibold">
              <a href={`#/architecture/component/${encodeURIComponent(component.name)}`}
                >{component.name}</a
              >
            </h3>
            <p>{component.responsibility}</p>
            {#if component.interfaces.length}
              <p data-component-interfaces>Interfaces: {component.interfaces.join(", ")}</p>
            {/if}
            {@render notes(component.decisions, component.constraints)}
          </div>
        {/each}
      </div>
    {/each}
    {#if architecture.view.interfaces.length}
      <h2 class="ptitle">Interfaces</h2>
    {/if}
    {#each architecture.view.interfaces as iface (iface.name)}
      <div data-architecture-interface={iface.name}>
        <h3 class="font-semibold">
          <a href={`#/architecture/interface/${encodeURIComponent(iface.name)}`}>{iface.name}</a>
        </h3>
        <p>{iface.provides}</p>
        <p data-interface-connects>Connects: {iface.connects.join(", ")}</p>
        {@render notes(iface.decisions, iface.constraints)}
      </div>
    {/each}
  {/if}
</section>
