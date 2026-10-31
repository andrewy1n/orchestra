// @vitest-environment jsdom
import { flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import TaskGraphBoard from "./TaskGraphBoard.svelte";
import { buildWaveGraph, type GraphTask } from "./taskGraph";

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	globalThis.ResizeObserver = class {
		observe() {}
		unobserve() {}
		disconnect() {}
	};
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	document.body.innerHTML = "";
});

function tasksByWave(sizes: number[]): GraphTask[] {
	return sizes.flatMap((size, wave) =>
		Array.from({ length: size }, (_, i) => ({
			id: `t-${wave}-${i}`,
			subject: `t-${wave}-${i}`,
			title: `Task ${wave}-${i}`,
			status: "ready",
			wave: wave + 1,
			depends_on: [],
		})),
	);
}

function canvasHeight(sizes: number[]): number {
	mounted = mount(TaskGraphBoard, {
		target: document.body,
		props: { graph: buildWaveGraph(tasksByWave(sizes)), onselect: () => {} },
	});
	flushSync();
	const flow = document.querySelector<HTMLElement>(".task-graph-flow");
	if (!flow) throw new Error("graph canvas missing");
	return Number.parseFloat(flow.style.height);
}

describe("graph height", () => {
	it("R1 a graph with one task per wave is at most 200px tall", () => {
		expect(canvasHeight([1, 1, 1])).toBeLessThanOrEqual(200);
	});

	it("R2 a four-task wave is at least 100px taller than a one-task wave", () => {
		const narrow = canvasHeight([1, 1, 1]);
		unmount(mounted as ReturnType<typeof mount>);
		document.body.innerHTML = "";
		const wide = canvasHeight([1, 4, 1]);
		expect(wide - narrow).toBeGreaterThanOrEqual(100);
	});

	it("R3 a very wide wave never makes the canvas taller than 480px", () => {
		expect(canvasHeight([1, 12, 1])).toBeLessThanOrEqual(480);
	});
});
