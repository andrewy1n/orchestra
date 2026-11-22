<script lang="ts">
  import { onMount } from "svelte";

  type Mode = "ok" | "throw" | "console-error" | "reject" | "error-event";
  let { mode = "ok" }: { mode?: Mode } = $props();

  function failDuringSetup() {
    if (mode === "throw") throw new Error("fixture mount failure");
    if (mode === "console-error") console.error("fixture console error");
  }
  failDuringSetup();

  onMount(() => {
    if (mode === "reject") {
      const event = new Event("unhandledrejection", { cancelable: true });
      Object.defineProperty(event, "reason", {
        value: new Error("fixture rejection"),
      });
      window.dispatchEvent(event);
    }
    if (mode === "error-event") {
      window.dispatchEvent(
        new ErrorEvent("error", { error: new Error("fixture error event") }),
      );
    }
  });
</script>

<p data-fixture>{mode}</p>
