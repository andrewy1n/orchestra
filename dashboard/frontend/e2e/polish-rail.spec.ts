/// <reference lib="dom" />
import { expect, test } from "@playwright/test";

test("R17 a rail item name renders at a font size of 14px", async ({
	page,
}) => {
	await page.goto("/#/phase/e2e-alpha/e2e-phase");
	const name = page.locator("nav.rail [data-rail-item] .name").first();
	await expect(name).toBeVisible();
	const size = await name.evaluate((el) => getComputedStyle(el).fontSize);
	expect(size).toBe("14px");
});
