<script lang="ts">
  import {
    Controls,
    type Edge,
    MarkerType,
    type Node,
    type NodeTypes,
    SvelteFlow,
  } from "@xyflow/svelte";
  import "@xyflow/svelte/dist/style.css";
  import TaskFlowNode from "./TaskFlowNode.svelte";
  import {
    graphHeight,
    NODE_H,
    NODE_W,
    toFlow,
    type WaveGraph,
    widestWave,
  } from "./taskGraph";

  if (typeof window !== "undefined" && typeof window.ResizeObserver !== "function") {
    window.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    } as typeof ResizeObserver;
  }

  if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
    window.matchMedia = (query: string) =>
      ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as MediaQueryList;
  }

  let {
    graph,
    onselect,
    colorMode = "light",
  }: {
    graph: WaveGraph;
    onselect: (id: string) => void;
    colorMode?: "light" | "dark" | "system";
  } = $props();

  const legend = $derived.by(() => {
    const present = new Set<string>();
    for (const lane of graph.lanes) {
      for (const node of lane.nodes) present.add(node.signal);
    }
    const items = [
      { signal: "done", label: "Done" },
      { signal: "run", label: "Running" },
      { signal: "ready", label: "Ready" },
      { signal: "wait", label: "Waiting" },
    ];
    return items.filter((item) => present.has(item.signal));
  });

  const nodeTypes: NodeTypes = { task: TaskFlowNode };
  const model = $derived(toFlow(graph));

  let boardEl: HTMLDivElement | undefined = $state();
  let boardWidth = $state(0);

  $effect(() => {
    const el = boardEl;
    if (!el || typeof ResizeObserver !== "function") return;
    const observer = new ResizeObserver(() => {
      boardWidth = el.clientWidth;
    });
    observer.observe(el);
    boardWidth = el.clientWidth;
    return () => observer.disconnect();
  });

  const stacked = $derived(boardWidth > 0 && boardWidth < 800);
  const nodeW = $derived(
    stacked ? Math.min(NODE_W, Math.max(160, boardWidth - 32)) : NODE_W,
  );
  const placed = $derived.by(() => {
    if (!stacked) return model.nodes;
    let y = 8;
    const rows = [];
    for (const lane of graph.lanes) {
      for (const node of lane.nodes) {
        rows.push({
          id: node.id,
          label: node.label,
          status: node.status,
          signal: node.signal,
          position: { x: 8, y },
        });
        y += NODE_H + 16;
      }
    }
    return rows;
  });
  const flowHeight = $derived.by(() => {
    if (!stacked) return graphHeight(widestWave(graph));
    const last = placed[placed.length - 1];
    return last ? last.position.y + NODE_H + 16 : 120;
  });

  let nodes = $state.raw<Node[]>([]);
  let edges = $state.raw<Edge[]>([]);
  let pointerOrigin: { x: number; y: number } | null = null;

  const fitViewOptions = { padding: 0.12, minZoom: 0.2, maxZoom: 1 };

  $effect(() => {
    const el = boardEl;
    if (!el) return;
    const down = (event: PointerEvent) => {
      pointerOrigin = { x: event.clientX, y: event.clientY };
    };
    el.addEventListener("pointerdown", down);
    return () => el.removeEventListener("pointerdown", down);
  });

  function onNodeClick({
    node,
    event,
  }: {
    node: Node;
    event: MouseEvent | TouchEvent;
  }) {
    if ("clientX" in event && pointerOrigin) {
      const dx = event.clientX - pointerOrigin.x;
      const dy = event.clientY - pointerOrigin.y;
      if (dx * dx + dy * dy > 16) return;
    }
    onselect(node.id);
  }

  $effect(() => {
    const source = placed;
    const width = nodeW;
    nodes = source.map((node) => ({
      id: node.id,
      type: "task",
      position: node.position,
      data: {
        label: node.label,
        status: node.status,
        signal: node.signal,
      },
      width,
      height: NODE_H,
      initialWidth: width,
      initialHeight: NODE_H,
      draggable: false,
      connectable: false,
      selectable: true,
    }));
    edges = model.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: stacked ? "down" : edge.sourceHandle,
      targetHandle: stacked ? "up" : edge.targetHandle,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      class: edge.kind === "flow" ? "task-edge-flow" : "task-edge",
    }));
  });
</script>

<div class="task-graph" data-task-graph>
  <div class="task-graph-head">
    <span class="section-title">Workflow</span>
    {#if legend.length}
      <div class="task-graph-legend">
        {#each legend as item (item.signal)}
          <span class="legend-item signal-{item.signal}">{item.label}</span>
        {/each}
      </div>
    {/if}
  </div>
  <div class="task-graph-board" bind:this={boardEl}>
    <div class="task-graph-lanes" class:is-fitted={!stacked}>
      {#each graph.lanes as lane (lane.wave)}
        <span data-graph-lane={lane.wave}>wave {lane.wave}</span>
      {/each}
    </div>
    <SvelteFlow
      bind:nodes
      bind:edges
      {nodeTypes}
      class="task-graph-flow"
      height={flowHeight}
      fitView={!stacked}
      {fitViewOptions}
      minZoom={0.2}
      maxZoom={2}
      colorMode={colorMode}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      panOnDrag={true}
      zoomOnScroll={false}
      zoomOnPinch={true}
      zoomOnDoubleClick={false}
      preventScrolling={false}
      deleteKey={null}
      defaultMarkerColor={null}
      proOptions={{ hideAttribution: true }}
      onnodeclick={onNodeClick}
    >
      <Controls
        showLock={false}
        {fitViewOptions}
        position="bottom-right"
        aria-label="Workflow view"
      />
    </SvelteFlow>
  </div>
</div>
