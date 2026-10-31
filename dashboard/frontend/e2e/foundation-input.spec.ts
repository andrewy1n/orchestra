/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";
const STATUS_TAB = "[data-status-tabs] [data-slot=tabs-trigger]";
const MIN_TOUCH_HEIGHT = 44;

async function openPhase(page: Page) {
	await page.goto(PHASE_URL);
	await expect(page.locator(STATUS_TAB).first()).toBeVisible();
}

test.describe("coarse pointer", () => {
	test.use({ hasTouch: true, isMobile: true });

	test("R30 a status tab is at least 44px tall on a coarse pointer", async ({
		page,
	}) => {
		await openPhase(page);
		expect(
			await page.evaluate(() => matchMedia("(pointer: coarse)").matches),
		).toBe(true);
		const heights = await page
			.locator(STATUS_TAB)
			.evaluateAll((tabs) =>
				tabs.map((tab) => tab.getBoundingClientRect().height),
			);
		expect(heights.length).toBeGreaterThan(1);
		for (const height of heights) {
			expect(height).toBeGreaterThanOrEqual(MIN_TOUCH_HEIGHT);
		}
	});
});

test.describe("keyboard", () => {
	test("R31 ArrowRight on a focused status tab selects the next status tab", async ({
		page,
	}) => {
		await openPhase(page);
		const tabs = page.locator(STATUS_TAB);
		const first = tabs.first();
		await first.focus();
		await expect(first).toHaveAttribute("aria-selected", "true");
		await page.keyboard.press("ArrowRight");
		const next = tabs.nth(1);
		await expect(next).toHaveAttribute("aria-selected", "true");
		await expect(first).toHaveAttribute("aria-selected", "false");
		await expect(next).toBeFocused();
		const label = ((await next.textContent()) ?? "").match(/\((\d+)\)/);
		expect(label).not.toBeNull();
		await expect(page.locator("[data-task]")).toHaveCount(
			Number(label?.[1] ?? Number.NaN),
		);
	});

	test("R32 exactly one status tab is in the Tab order", async ({ page }) => {
		await openPhase(page);
		const tabs = page.locator(STATUS_TAB);
		expect(await tabs.count()).toBeGreaterThan(1);
		await expect(page.locator(`${STATUS_TAB}[tabindex="0"]`)).toHaveCount(1);
	});
});
