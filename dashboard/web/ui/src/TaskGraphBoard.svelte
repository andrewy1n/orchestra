<script lang="ts">
  import {
    MarkerType,
    SvelteFlow,
    type Edge,
    type Node,
    type NodeTypes,
  } from "@xyflow/svelte";
  import "@xyflow/svelte/dist/style.css";
  import TaskFlowNode from "./TaskFlowNode.svelte";
  import { NODE_H, NODE_W, toFlow, type WaveGraph } from "./taskGraph";

  let { graph, onselect }: { graph: WaveGraph; onselect: (id: string) => void } =
    $props();

  const nodeTypes: NodeTypes = { task: TaskFlowNode };
  const model = $derived(toFlow(graph));

  let nodes = $state.raw<Node[]>([]);
  let edges = $state.raw<Edge[]>([]);

  $effect(() => {
    nodes = model.nodes.map((node) => ({
      id: node.id,
      type: "task",
      position: node.position,
      data: {
        label: node.label,
        status: node.status,
        signal: node.signal,
      },
      width: NODE_W,
      height: NODE_H,
      initialWidth: NODE_W,
      initialHeight: NODE_H,
      draggable: false,
      connectable: false,
      selectable: false,
    }));
    edges = model.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      class: edge.kind === "flow" ? "task-edge-flow" : "task-edge",
    }));
  });
</script>

<div class="task-graph" data-task-graph>
  <div class="task-graph-head">
    <span class="section-title">Workflow</span>
    <div class="task-graph-legend" aria-hidden="true">
      <span class="legend-item signal-done">done</span>
      <span class="legend-item signal-run">run</span>
      <span class="legend-item signal-ready">ready</span>
      <span class="legend-item signal-wait">wait</span>
    </div>
  </div>
  <div class="task-graph-board">
    <div
      class="task-graph-lanes"
      style:width="{model.width}px"
      style:gap="{model.colGap}px"
    >
      {#each graph.lanes as lane (lane.wave)}
        <span data-graph-lane={lane.wave} style:width="{model.nodeW}px">wave {lane.wave}</span>
      {/each}
    </div>
    <SvelteFlow
      bind:nodes
      bind:edges
      {nodeTypes}
      class="task-graph-flow"
      width={model.width}
      height={model.height}
      colorMode="system"
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      panOnDrag={false}
      zoomOnScroll={false}
      zoomOnPinch={false}
      zoomOnDoubleClick={false}
      preventScrolling={false}
      deleteKey={null}
      defaultMarkerColor={null}
      proOptions={{ hideAttribution: true }}
      onnodeclick={({ node }) => onselect(node.id)}
    />
  </div>
</div>
