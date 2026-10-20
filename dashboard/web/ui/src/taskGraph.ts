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

function waveKey(wave: number | null | undefined): string {
  if (wave == null || wave === ("" as unknown as number)) return "—";
  return String(wave);
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

  const nodes: GraphNode[] = [];
  const lanes = waveOrder.map((wave, lane) => {
    const group = laneMap.get(wave) ?? [];
    const laneNodes = group.map((task, index) => {
      const label = (task.title || task.subject || task.id).trim();
      const node: GraphNode = {
        id: task.id,
        label,
        status: task.status,
        wave,
        lane,
        index,
      };
      nodes.push(node);
      return node;
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
