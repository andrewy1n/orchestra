import { expect, test } from "@playwright/test";

test("the packaged dashboard shows the seeded effort", async ({ page }) => {
	await page.goto("/");
	await expect(page.getByText("e2e-alpha").first()).toBeVisible();
});
