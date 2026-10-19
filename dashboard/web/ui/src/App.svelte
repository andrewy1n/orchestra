<script lang="ts">
  import { onMount } from "svelte";
  import { currentRoute, routeLabel, type Route } from "./router";
  import { applyTheme, DEFAULT_THEME, toggle, type Theme } from "./theme";

  // A fresh load is always light; the control switches the whole page.
  let theme: Theme = $state(DEFAULT_THEME);
  let route: Route = $state(currentRoute());

  applyTheme(theme);

  function setTheme(next: Theme) {
    theme = next;
    applyTheme(next);
  }

  function onToggleTheme() {
    setTheme(toggle(theme));
  }

  onMount(() => {
    const sync = () => (route = currentRoute());
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  });
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">orchestra <span class="brand-sub">dashboard</span></div>
    <div class="crumbs" aria-live="polite">{routeLabel(route)}</div>
    <div class="top-actions">
      <button
        type="button"
        class="ghost"
        data-act="theme"
        aria-label="Theme"
        aria-pressed={theme === "dark"}
        title="Theme (t)"
        onclick={onToggleTheme}
      >
        ◐
      </button>
    </div>
  </header>

  <div class="layout">
    <nav class="rail" aria-label="Efforts"></nav>
    <main class="main" data-route={route.name}></main>
    <aside class="side" aria-label="Details"></aside>
  </div>

  <footer class="statusbar"></footer>
</div>
