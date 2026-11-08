import { expect, test } from "@playwright/test";

test("R1 the root shows the hub", async ({ page }) => {
	await page.goto("/");
	await expect(page.locator("main [data-hub]")).toBeVisible();
});
