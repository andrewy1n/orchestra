<script lang="ts">
  import { navigation } from "$lib/state/route.svelte";

  const onWork = $derived(navigation.route.name === "home");
  const onArchitecture = $derived(navigation.route.name === "architecture");
</script>

<nav class="top-tabs" data-top-tabs aria-label="Sections">
  <a
    class="top-tab"
    data-tab="work"
    href="#/"
    aria-current={onWork ? "page" : undefined}>Work</a
  >
  <a
    class="top-tab"
    data-tab="product"
    href="#/areas"
    aria-current={onWork || onArchitecture ? undefined : "page"}>Product</a
  >
  <a
    class="top-tab"
    data-tab="architecture"
    href="#/architecture"
    aria-current={onArchitecture ? "page" : undefined}>Architecture</a
  >
</nav>
