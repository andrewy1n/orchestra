/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const JOURNAL_URL = "/#/journal/e2e-alpha";

async function openJournal(page: Page) {
	await page.setViewportSize({ width: 1280, height: 900 });
	await page.goto(JOURNAL_URL);
	await expect(page.locator("[data-journal-screen]")).toBeVisible();
	await expect(page.locator("[data-journal-list]")).toBeVisible();
}

test("R12 the journal title is an h1 at 20px", async ({ page }) => {
	await openJournal(page);
	const title = page.locator("[data-journal-screen] h1");
	await expect(title).toHaveCount(1);
	await expect(title).toContainText("Journal");
	await expect(title).toHaveCSS("font-size", "20px");
});

test("R13 the journal Back control is a shadcn Button", async ({ page }) => {
	await openJournal(page);
	const back = page.locator('[data-act="close-journal"]');
	await expect(back).toHaveCount(1);
	await expect(back).toHaveAttribute("data-slot", "button");
});

test("R14 the journal filter is a shadcn Input 36px high", async ({ page }) => {
	await openJournal(page);
	const filter = page.locator("[data-journal-filter]");
	await expect(filter).toHaveAttribute("data-slot", "input");
	const box = await filter.boundingBox();
	expect(box?.height).toBe(36);
});

test("R15 the journal list fills the main column at 1280px", async ({
	page,
}) => {
	await openJournal(page);
	const widths = await page.evaluate(() => {
		const main = document.querySelector("main.main");
		const list = document.querySelector("[data-journal-list]");
		if (!main || !list) throw new Error("journal layout is missing");
		return {
			main: main.getBoundingClientRect().width,
			list: list.getBoundingClientRect().width,
		};
	});
	expect(widths.list / widths.main).toBeGreaterThanOrEqual(0.9);
});
