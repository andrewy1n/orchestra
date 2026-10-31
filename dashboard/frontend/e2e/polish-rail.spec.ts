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

test("R17 dark: a rail item name renders at a font size of 14px", async ({
	page,
}) => {
	await page.goto("/#/phase/e2e-alpha/e2e-phase");
	await page.locator(".theme-switch").click();
	await expect(page.locator("html")).toHaveClass(/(^|\s)dark(\s|$)/);
	const name = page.locator("nav.rail [data-rail-item] .name").first();
	await expect(name).toBeVisible();
	const size = await name.evaluate((el) => getComputedStyle(el).fontSize);
	expect(size).toBe("14px");
});

test("R18 the rail toggle reads Show N done with the count and Hide done when open", async ({
	page,
}) => {
	await page.goto("/#/phase/e2e-alpha/e2e-phase");
	const toggle = page.locator("[data-act='show-done-phases']");
	await expect(toggle).toHaveText("Show 1 done");
	await toggle.click();
	await expect(toggle).toHaveText("Hide done");
	await toggle.click();
	await expect(toggle).toHaveText("Show 1 done");
});
