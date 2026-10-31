/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const SELECTED = "[data-status-tabs] [data-tab][aria-selected='true']";

async function open(page: Page, phase: string) {
	await page.goto(`/#/phase/e2e-alpha/${phase}`);
	await expect(
		page.locator("[data-status-tabs] [data-tab]").first(),
	).toBeVisible();
}

test("R4 a phase with only done tasks opens on the Done tab", async ({
	page,
}) => {
	await open(page, "e2e-done");
	await expect(page.locator(SELECTED)).toHaveCount(1);
	await expect(page.locator(SELECTED)).toHaveAttribute("data-tab", "done");
});

test("R5 a phase with an active task opens on the Active tab", async ({
	page,
}) => {
	await open(page, "e2e-phase");
	await expect(page.locator(SELECTED)).toHaveCount(1);
	await expect(page.locator(SELECTED)).toHaveAttribute("data-tab", "active");
});

test("R6 a clicked status tab stays selected after the phase data refreshes", async ({
	page,
}) => {
	await open(page, "e2e-done");
	await page.locator("[data-status-tabs] [data-tab='all']").click();
	await expect(page.locator(SELECTED)).toHaveAttribute("data-tab", "all");
	await page.route("**/api/token", (route) =>
		route.fulfill({ json: { token: "e2e-refresh" } }),
	);
	await page.waitForResponse((response) =>
		response.url().includes("/api/snapshot"),
	);
	await expect(page.locator(SELECTED)).toHaveAttribute("data-tab", "all");
});
