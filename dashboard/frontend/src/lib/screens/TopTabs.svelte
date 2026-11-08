<script lang="ts">
  import { navigation } from "$lib/state/route.svelte";

  const onWork = $derived(navigation.route.name === "home");
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
    aria-current={onWork ? undefined : "page"}>Product</a
  >
</nav>
