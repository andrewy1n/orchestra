/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

async function canvasHeight(page: Page, phase: string): Promise<number> {
	await page.setViewportSize({ width: 1280, height: 900 });
	await page.goto(`/#/phase/e2e-alpha/${phase}`);
	const flow = page.locator(".task-graph-flow");
	await expect(flow).toBeVisible();
	await expect(
		page.locator(".task-graph-flow .svelte-flow__node"),
	).not.toHaveCount(0);
	const board = await page
		.locator(".task-graph-board")
		.evaluate((el) => el.clientWidth);
	expect(board).toBeGreaterThanOrEqual(800);
	return flow.evaluate((el) => Number.parseFloat(getComputedStyle(el).height));
}

test("R1 a graph with one task per wave is at most 200px tall", async ({
	page,
}) => {
	expect(await canvasHeight(page, "e2e-chain")).toBeLessThanOrEqual(200);
});

test("R2 a wave of several tasks makes the canvas at least 100px taller than a one-task wave", async ({
	page,
}) => {
	const narrow = await canvasHeight(page, "e2e-chain");
	const wide = await canvasHeight(page, "e2e-wide");
	expect(wide - narrow).toBeGreaterThanOrEqual(100);
});

test("R3 the graph canvas is never taller than 480px on a wide board", async ({
	page,
}) => {
	expect(await canvasHeight(page, "e2e-wide")).toBeLessThanOrEqual(480);
});
