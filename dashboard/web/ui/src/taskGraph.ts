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
  /** Unfinished dependency subjects (legacy / waits_on). */
  waits_on?: string[] | null;
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
  /** Explicit dependency vs inferred wave pipeline. */
  kind: "depends" | "flow";
}

export interface WaveGraph {
  lanes: { wave: string; nodes: GraphNode[] }[];
  edges: GraphEdge[];
  /** False when the graph should not render (≤2 tasks). */
  show: boolean;
}

export const NODE_W = 232;
export const NODE_H = 84;
const COL_GAP = 80;
const ROW_GAP = 24;

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

function collectDependsIds(task: GraphTask, bySubject: Map<string, string>): string[] {
  const ids = new Set<string>();
  for (const dep of task.depends_on ?? []) {
    if (dep) ids.add(dep);
  }
  for (const subject of task.waits_on ?? []) {
    const id = bySubject.get(subject);
    if (id) ids.add(id);
  }
  return [...ids];
}

/**
 * Build columns by wave (left → right) and edges from depends_on / waits_on.
 * If no dependency edges exist, infer flow edges between adjacent waves so the
 * graph still reads as a workflow. Returns `show: false` when tasks.length <= 2.
 */
export function buildWaveGraph(tasks: GraphTask[]): WaveGraph {
  if (tasks.length <= 2) {
    return { lanes: [], edges: [], show: false };
  }

  const bySubject = new Map<string, string>();
  for (const task of tasks) {
    if (task.subject) bySubject.set(task.subject, task.id);
  }

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
  const seen = new Set<string>();
  for (const task of tasks) {
    for (const dep of collectDependsIds(task, bySubject)) {
      if (!known.has(dep)) continue;
      const key = `${dep}->${task.id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push({ from: dep, to: task.id, kind: "depends" });
    }
  }

  // No recorded deps → still show workflow flow across adjacent waves.
  if (edges.length === 0 && lanes.length >= 2) {
    for (let i = 0; i < lanes.length - 1; i++) {
      const left = lanes[i]!;
      const right = lanes[i + 1]!;
      for (const from of left.nodes) {
        for (const to of right.nodes) {
          edges.push({ from: from.id, to: to.id, kind: "flow" });
        }
      }
    }
  }

  return { lanes, edges, show: true };
}

export interface FlowNodeModel {
  id: string;
  label: string;
  status: string;
  signal: string;
  position: { x: number; y: number };
}

export interface FlowEdgeModel {
  id: string;
  source: string;
  target: string;
  /** Side handles for the next wave; top handles when the edge skips a column. */
  sourceHandle: "out" | "skip-out";
  targetHandle: "in" | "skip-in";
  kind: GraphEdge["kind"];
}

/** Place tasks in wave columns. Svelte Flow draws the edges and arrowheads. */
export function toFlow(graph: WaveGraph): {
  nodes: FlowNodeModel[];
  edges: FlowEdgeModel[];
  width: number;
  height: number;
} {
  const byId = new Map<string, GraphNode>();
  for (const lane of graph.lanes) {
    for (const node of lane.nodes) byId.set(node.id, node);
  }
  const skip = graph.edges.some((edge) => {
    const from = byId.get(edge.from);
    const to = byId.get(edge.to);
    return !!from && !!to && Math.abs(from.lane - to.lane) > 1;
  });
  const top = skip ? 64 : 8;
  let bottom = top + NODE_H;
  const nodes: FlowNodeModel[] = [];
  for (const lane of graph.lanes) {
    for (const node of lane.nodes) {
      const y = top + node.index * (NODE_H + ROW_GAP);
      bottom = Math.max(bottom, y + NODE_H);
      nodes.push({
        id: node.id,
        label: node.label,
        status: node.status,
        signal: node.signal,
        position: { x: node.lane * (NODE_W + COL_GAP), y },
      });
    }
  }
  const edges: FlowEdgeModel[] = [];
  for (const edge of graph.edges) {
    const from = byId.get(edge.from);
    const to = byId.get(edge.to);
    if (!from || !to) continue;
    const spans = Math.abs(from.lane - to.lane) > 1;
    edges.push({
      id: `${edge.from}->${edge.to}`,
      source: edge.from,
      target: edge.to,
      sourceHandle: spans ? "skip-out" : "out",
      targetHandle: spans ? "skip-in" : "in",
      kind: edge.kind,
    });
  }
  const laneCount = Math.max(graph.lanes.length, 1);
  return {
    nodes,
    edges,
    nodeW: NODE_W,
    colGap: COL_GAP,
    width: laneCount * NODE_W + Math.max(0, laneCount - 1) * COL_GAP + 24,
    height: bottom + 20,
  };
}
