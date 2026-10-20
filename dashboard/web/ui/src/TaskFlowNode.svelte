<script lang="ts">
  import { Handle, Position, type NodeProps } from "@xyflow/svelte";

  let { id, data }: NodeProps = $props();
</script>

<button
  type="button"
  class="graph-node signal-{data.signal}"
  data-graph-node={id}
  data-status={data.status}
  data-signal={data.signal}
  aria-label={String(data.label ?? "")}
>
  <Handle
    id="in"
    type="target"
    position={Position.Left}
    class="task-handle"
    aria-hidden="true"
  />
  <Handle
    id="skip-in"
    type="target"
    position={Position.Top}
    class="task-handle"
    style="left: 72%;"
    aria-hidden="true"
  />
  <span class="graph-signal" aria-hidden="true"></span>
  <span class="graph-node-body">
    <span class="graph-node-title">{data.label}</span>
    <span class="graph-node-meta">{data.status}</span>
  </span>
  <Handle
    id="up"
    type="target"
    position={Position.Top}
    class="task-handle"
    aria-hidden="true"
  />
  <Handle
    id="out"
    type="source"
    position={Position.Right}
    class="task-handle"
    aria-hidden="true"
  />
  <Handle
    id="down"
    type="source"
    position={Position.Bottom}
    class="task-handle"
    aria-hidden="true"
  />
  <Handle
    id="skip-out"
    type="source"
    position={Position.Top}
    class="task-handle"
    style="left: 28%;"
    aria-hidden="true"
  />
</button>
