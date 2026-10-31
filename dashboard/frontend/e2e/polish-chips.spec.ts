/// <reference lib="dom" />
import { expect, test } from "@playwright/test";

test("R16 a phase state chip and a requirement chip have the same computed height", async ({
	page,
}) => {
	await page.goto("/#/phase/e2e-alpha/e2e-phase");
	const stateChip = page
		.locator("[data-phase-chips] [data-slot=badge]")
		.first();
	const reqChip = page.locator("[data-phase-req]").first();
	await expect(stateChip).toBeVisible();
	await expect(reqChip).toBeVisible();
	const height = (chip: typeof stateChip) =>
		chip.evaluate((el) => getComputedStyle(el).height);
	const state = await height(stateChip);
	expect(state).not.toBe("auto");
	expect(await height(reqChip)).toBe(state);
});
