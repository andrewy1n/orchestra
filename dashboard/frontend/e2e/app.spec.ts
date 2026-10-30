import { expect, test } from "@playwright/test";

test("the packaged dashboard shows the seeded effort", async ({ page }) => {
	await page.goto("/#/effort/e2e-alpha");
	await expect(page.getByText("e2e-alpha").first()).toBeVisible();
});

test("R28 the product index shows the seeded area card", async ({ page }) => {
	await page.goto("/");
	await expect(page.locator('[data-area-card="e2e-area"]')).toBeVisible();
});

test("R29 a click on the area card opens the area page", async ({ page }) => {
	await page.goto("/");
	await page.locator('[data-area-card="e2e-area"]').click();
	await expect(page).toHaveURL(/#\/area\/e2e-area$/);
});
