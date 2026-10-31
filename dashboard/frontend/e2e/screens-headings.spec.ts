/// <reference lib="dom" />
import { expect, test } from "@playwright/test";

const AREA_URL = "/#/area/e2e-area";

test("R7 the area page has one h1 holding the area title", async ({ page }) => {
	await page.goto(AREA_URL);
	await expect(page.locator("[data-area-screen]")).toBeVisible();
	const headings = page.locator("main h1");
	await expect(headings).toHaveCount(1);
	await expect(headings).toContainText("E2E area");
});

test("R8 the area page h1 renders at 20px", async ({ page }) => {
	await page.goto(AREA_URL);
	await expect(page.locator("[data-area-screen]")).toBeVisible();
	await expect(page.locator("main h1")).toHaveCSS("font-size", "20px");
});

test("R9 the product home has one h1 reading Areas", async ({ page }) => {
	await page.goto("/");
	await expect(page.locator("[data-product-index]")).toBeVisible();
	const headings = page.locator("main h1");
	await expect(headings).toHaveCount(1);
	await expect(headings).toHaveText("Areas");
});

test("R10 home area cards in one row share a height", async ({ page }) => {
	await page.goto("/");
	const cards = page.locator("[data-area-card]");
	await expect(cards.first()).toBeVisible();
	const heights = await cards.evaluateAll((els) =>
		els.map((el) => {
			const box = el.getBoundingClientRect();
			return { top: Math.round(box.top), height: Math.round(box.height) };
		}),
	);
	const byRow = new Map<number, number[]>();
	for (const card of heights) {
		const row = byRow.get(card.top) ?? [];
		row.push(card.height);
		byRow.set(card.top, row);
	}
	for (const row of byRow.values()) {
		expect(new Set(row).size).toBe(1);
	}
});

test("R11 a home area card shows counts and no effort names", async ({
	page,
}) => {
	await page.goto("/");
	const card = page.locator('[data-area-card="e2e-area"]');
	await expect(card).toBeVisible();
	await expect(card.locator("[data-card-effort]")).toHaveCount(0);
	await expect(card.locator("[data-card-efforts]")).toContainText("effort");
	await expect(card.locator("[data-card-scope]")).toBeVisible();
});
