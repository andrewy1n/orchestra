<script lang="ts">
  import { effortHref } from "../../detail";
  import type { EffortView } from "../../types";

  let { view }: { view: EffortView } = $props();
</script>

<a class="lrow clickable effort-row" data-effort-row={view.effort} href={effortHref(view.effort)}>
  <span class="kind accent">{view.kind}</span>
  <span class="text"><strong>{view.effort}</strong>{view.goal ? ` — ${view.goal}` : ""}</span>
  <span class="meta" data-effort-needs>{view.needs_you.length} needs you</span>
</a>
