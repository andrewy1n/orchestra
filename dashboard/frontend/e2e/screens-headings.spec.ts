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

test("R10 each home area card aligns to the start of its grid cell", async ({
	page,
}) => {
	await page.goto("/");
	const cards = page.locator("[data-area-card]");
	await expect(cards.first()).toBeVisible();
	const count = await cards.count();
	for (let index = 0; index < count; index += 1) {
		await expect(cards.nth(index)).toHaveCSS("align-self", "start");
	}
});

test("R11 each effort name in a home area card differs in colour from the card text", async ({
	page,
}) => {
	await page.goto("/");
	const card = page.locator('[data-area-card="e2e-area"]');
	await expect(card).toBeVisible();
	const efforts = card.locator("[data-card-effort]");
	await expect(efforts.first()).toBeVisible();
	const cardColour = await card.evaluate((el) => getComputedStyle(el).color);
	const count = await efforts.count();
	for (let index = 0; index < count; index += 1) {
		await expect(efforts.nth(index)).not.toHaveCSS("color", cardColour);
	}
});
