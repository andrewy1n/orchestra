/// <reference lib="dom" />
import { expect, type Locator, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";

async function openStatusTabs(page: Page) {
	await page.goto(PHASE_URL);
	await expect(
		page.locator("[data-status-tabs] [data-tab]").first(),
	).toBeVisible();
}

function fontSize(locator: Locator) {
	return locator.evaluate((el) => getComputedStyle(el).fontSize);
}

test("R16 a status tab count renders at a font size of 12px", async ({
	page,
}) => {
	await openStatusTabs(page);
	const count = page
		.locator('[data-status-tabs] [data-tab="all"]')
		.getByText(/^\(\d+\)$/);
	await expect(count).toHaveCount(1);
	expect(await fontSize(count)).toBe("12px");
});

test("R21 a status tab label renders at a font size of 14px", async ({
	page,
}) => {
	await openStatusTabs(page);
	const label = page
		.locator('[data-status-tabs] [data-tab="all"]')
		.getByText("All", { exact: true });
	await expect(label).toHaveCount(1);
	expect(await fontSize(label)).toBe("14px");
});
