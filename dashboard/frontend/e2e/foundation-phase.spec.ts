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

test("R19 the task table is a shadcn table as wide as its container", async ({
	page,
}) => {
	await openStatusTabs(page);
	await page.locator('[data-status-tabs] [data-tab="all"]').click();
	const table = page.locator("[data-task-table]");
	await expect(table).toHaveCount(1);
	await expect(table.locator("[data-task]")).toHaveCount(1);
	expect(await table.evaluate((el) => el.tagName)).toBe("TABLE");
	expect(await table.getAttribute("data-slot")).toBe("table");
	const widths = await table.evaluate((el) => {
		const container = el.closest("div.overflow-hidden.rounded-md.border");
		if (!container) return { table: 0, container: 0 };
		const style = getComputedStyle(container);
		return {
			table: el.getBoundingClientRect().width,
			container:
				container.getBoundingClientRect().width -
				Number.parseFloat(style.borderLeftWidth) -
				Number.parseFloat(style.borderRightWidth),
		};
	});
	expect(widths.container).toBeGreaterThan(0);
	expect(widths.table).toBeCloseTo(widths.container, 1);
});
