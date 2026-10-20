<script lang="ts">
  import { Handle, Position, type NodeProps } from "@xyflow/svelte";

  let { id, data }: NodeProps = $props();
</script>

<div
  class="graph-node signal-{data.signal}"
  data-graph-node={id}
  data-status={data.status}
  data-signal={data.signal}
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
    <span class="graph-node-title" title={data.label}>{data.label}</span>
    <span class="graph-node-meta">{data.signal}</span>
  </span>
  <Handle
    id="out"
    type="source"
    position={Position.Right}
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
</div>
