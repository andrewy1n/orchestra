<script lang="ts">
  import { onMount, untrack } from "svelte";
  import Area from "$lib/screens/Area.svelte";
  import Breadcrumb from "$lib/screens/Breadcrumb.svelte";
  import ConfirmModal from "$lib/screens/ConfirmModal.svelte";
  import Home from "$lib/screens/Home.svelte";
  import Hub from "$lib/screens/Hub.svelte";
  import Journal from "$lib/screens/Journal.svelte";
  import Overlay from "$lib/screens/Overlay.svelte";
  import PhasePage from "$lib/screens/PhasePage.svelte";
  import ProductIndex from "$lib/screens/ProductIndex.svelte";
  import Rail from "$lib/screens/Rail.svelte";
  import SideRail from "$lib/screens/SideRail.svelte";
  import StatusBar from "$lib/screens/StatusBar.svelte";
  import TopTabs from "$lib/screens/TopTabs.svelte";
  import { railItems, routePhase } from "$lib/state/areas";
  import { areas, bindAreas } from "$lib/state/areas.svelte";
  import { bindHub } from "$lib/state/hub.svelte";
  import { bindJournal } from "$lib/state/journal.svelte";
  import { handleKey } from "$lib/state/keys";
  import { bindOverlay, overlay } from "$lib/state/overlay.svelte";
  import { bindPhase } from "$lib/state/phase.svelte";
  import { bindPolling, polling } from "$lib/state/polling.svelte";
  import { navigation } from "$lib/state/route.svelte";
  import { effortName } from "./router";
  import { applyTheme, loadTheme, saveTheme, type Theme, toggle } from "./theme";

  let theme: Theme = $state(loadTheme());

  bindPolling();
  bindJournal();
  bindAreas();
  bindHub();
  bindOverlay();
  bindPhase();

  const needsSnapshot = $derived(navigation.route.name !== "home");
  const effort = $derived(polling.effort);
  const target = $derived(overlay.target);
  const onPhasePage = $derived(
    navigation.route.name === "phase" ||
      routePhase(navigation.route, polling.snapshot?.efforts ?? []) !== null,
  );
  const railLevel = $derived(
    railItems(
      navigation.route,
      polling.snapshot,
      areas.items,
      polling.selectedEffort,
    ).level,
  );

  $effect(() => {
    applyTheme(theme);
  });

  $effect(() => {
    const fetchSnapshot = needsSnapshot;
    return untrack(() => polling.start(fetchSnapshot));
  });

  function onToggleTheme() {
    theme = toggle(theme);
    saveTheme(theme);
  }

  onMount(() => {
    const stopRoute = navigation.listen();

    const onKey = (event: KeyboardEvent) => handleKey(event, onToggleTheme);
    window.addEventListener("keydown", onKey, true);

    return () => {
      stopRoute();
      window.removeEventListener("keydown", onKey, true);
    };
  });
</script>

<div class="app" inert={target || overlay.pendingWrite ? true : undefined}>
  <header class="topbar">
    <div class="brand">orchestra <span class="brand-sub">dashboard</span></div>
    <TopTabs />
    <div class="crumbs" aria-live="polite"><Breadcrumb /></div>
    <div class="top-actions">
      <button
        type="button"
        class="theme-switch"
        data-act="theme"
        role="switch"
        aria-checked={theme === "dark"}
        title="Theme (t)"
        onclick={onToggleTheme}
      >
        <span class="theme-track" aria-hidden="true"><span class="theme-thumb"></span></span>
        Dark
      </button>
    </div>
  </header>

  <div
    class="layout"
    class:no-rail={railLevel === "product"}
    class:no-side={railLevel !== "effort"}
  >
    {#if railLevel !== "product"}
      <input class="rail-toggle" id="rail-toggle" type="checkbox" />
      <Rail />
    {/if}

    <main class="main" data-route={navigation.route.name}>
      {#if navigation.route.name === "journal"}
        <Journal />
      {:else if navigation.route.name === "home"}
        <Hub />
      {:else if navigation.route.name === "areas"}
        <ProductIndex />
      {:else if navigation.route.name === "area"}
        <Area />
      {:else if onPhasePage}
        <PhasePage {theme} />
      {:else if navigation.route.name === "effort" && !effort}
        {#if polling.snapshot}
          <p class="empty-note">No effort named {effortName(navigation.route)}.</p>
        {/if}
      {:else if effort}
        <Home {effort} />
      {:else if !polling.loading && !polling.error}
        <p class="empty-note">No efforts in this store.</p>
      {/if}
    </main>

    {#if railLevel === "effort"}
      <SideRail />
    {/if}
    {#if railLevel !== "product"}
      <label class="rail-toggle-label" for="rail-toggle"
        >{railLevel === "area"
          ? "Areas"
          : railLevel === "phase"
            ? "Phases"
            : "Efforts"}</label
      >
    {/if}
  </div>

  <StatusBar />
</div>

<Overlay />
<ConfirmModal />
