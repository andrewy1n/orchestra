/**
 * Wave-lane dependency graph for phase Overview.
 */

export interface GraphTask {
  id: string;
  subject?: string;
  title?: string;
  status: string;
  wave?: number | null;
  depends_on?: string[] | null;
}

export interface GraphNode {
  id: string;
  label: string;
  status: string;
  /** Short status signal for the node badge. */
  signal: string;
  wave: string;
  lane: number;
  index: number;
}

export interface GraphEdge {
  from: string;
  to: string;
}

export interface WaveGraph {
  lanes: { wave: string; nodes: GraphNode[] }[];
  edges: GraphEdge[];
  /** False when the graph should not render (≤2 tasks). */
  show: boolean;
}

export interface LaidOutNode extends GraphNode {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface LaidOutEdge extends GraphEdge {
  /** SVG path `d` from source right-center to target left-center. */
  d: string;
}

export interface GraphLayout {
  width: number;
  height: number;
  nodeW: number;
  nodeH: number;
  nodes: LaidOutNode[];
  edges: LaidOutEdge[];
  lanes: { wave: string; x: number; label: string }[];
}

const NODE_W = 148;
const NODE_H = 44;
const COL_GAP = 56;
const ROW_GAP = 18;
const PAD_X = 20;
const PAD_Y = 36;

function waveKey(wave: number | null | undefined): string {
  if (wave == null || wave === ("" as unknown as number)) return "—";
  return String(wave);
}

/** Map task status → short workflow signal. */
export function statusSignal(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "done") return "done";
  if (s === "running" || s === "in_progress") return "run";
  if (s === "ready") return "ready";
  if (s === "waiting" || s === "blocked") return "wait";
  if (s === "planned") return "plan";
  return s.slice(0, 4) || "—";
}

/**
 * Build columns by wave (left → right) and edges from depends_on ids
 * among the given tasks. Returns `show: false` when tasks.length <= 2.
 */
export function buildWaveGraph(tasks: GraphTask[]): WaveGraph {
  if (tasks.length <= 2) {
    return { lanes: [], edges: [], show: false };
  }

  const byId = new Map(tasks.map((task) => [task.id, task]));
  const laneMap = new Map<string, GraphTask[]>();
  for (const task of tasks) {
    const key = waveKey(task.wave);
    const list = laneMap.get(key) ?? [];
    list.push(task);
    laneMap.set(key, list);
  }

  const waveOrder = [...laneMap.keys()].sort((a, b) => {
    if (a === "—") return 1;
    if (b === "—") return -1;
    return Number(a) - Number(b);
  });

  const lanes = waveOrder.map((wave, lane) => {
    const group = laneMap.get(wave) ?? [];
    const laneNodes = group.map((task, index) => {
      const label = (task.title || task.subject || task.id).trim();
      return {
        id: task.id,
        label,
        status: task.status,
        signal: statusSignal(task.status),
        wave,
        lane,
        index,
      } satisfies GraphNode;
    });
    return { wave, nodes: laneNodes };
  });

  const known = new Set(tasks.map((task) => task.id));
  const edges: GraphEdge[] = [];
  for (const task of tasks) {
    for (const dep of task.depends_on ?? []) {
      if (!known.has(dep) || !byId.has(dep)) continue;
      edges.push({ from: dep, to: task.id });
    }
  }

  return { lanes, edges, show: true };
}

/** Orthogonal-ish cubic path from the right of `from` to the left of `to`. */
function edgePath(
  from: { x: number; y: number; w: number; h: number },
  to: { x: number; y: number; h: number },
): string {
  const x1 = from.x + from.w;
  const y1 = from.y + from.h / 2;
  const x2 = to.x;
  const y2 = to.y + to.h / 2;
  const mid = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
}

/**
 * Place nodes in wave columns and build SVG edge paths that meet card edges
 * (not centers), so connectors read as a workflow.
 */
export function layoutWaveGraph(graph: WaveGraph): GraphLayout | null {
  if (!graph.show || graph.lanes.length === 0) return null;

  const colStride = NODE_W + COL_GAP;
  const rowStride = NODE_H + ROW_GAP;
  let maxRows = 1;
  const nodes: LaidOutNode[] = [];
  const lanes = graph.lanes.map((lane, laneIndex) => {
    maxRows = Math.max(maxRows, lane.nodes.length);
    const x = PAD_X + laneIndex * colStride;
    for (const node of lane.nodes) {
      nodes.push({
        ...node,
        x,
        y: PAD_Y + node.index * rowStride,
        w: NODE_W,
        h: NODE_H,
      });
    }
    return {
      wave: lane.wave,
      x: x + NODE_W / 2,
      label: lane.wave === "—" ? "wave —" : `wave ${lane.wave}`,
    };
  });

  const byId = new Map(nodes.map((node) => [node.id, node]));
  const edges: LaidOutEdge[] = [];
  for (const edge of graph.edges) {
    const from = byId.get(edge.from);
    const to = byId.get(edge.to);
    if (!from || !to) continue;
    edges.push({
      from: edge.from,
      to: edge.to,
      d: edgePath(from, to),
    });
  }

  const width = PAD_X * 2 + graph.lanes.length * colStride - COL_GAP;
  const height = PAD_Y + maxRows * rowStride - ROW_GAP + 16;
  return {
    width: Math.max(width, 280),
    height: Math.max(height, 100),
    nodeW: NODE_W,
    nodeH: NODE_H,
    nodes,
    edges,
    lanes,
  };
}
