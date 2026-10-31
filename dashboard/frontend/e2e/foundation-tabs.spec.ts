/// <reference lib="dom" />
import { expect, type Locator, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";

type Theme = "light" | "dark";

async function openPhase(page: Page, theme: Theme = "light") {
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-tab]").nth(1)).toBeVisible();
	if (theme === "dark") {
		await page.locator(".theme-switch").click();
		await expect(page.locator("html")).toHaveClass(/(^|\s)dark(\s|$)/);
		await page.evaluate(() =>
			Promise.all(
				document.getAnimations().map((animation) => animation.finished),
			),
		);
	}
}

function computed(locator: Locator, property: keyof CSSStyleDeclaration) {
	return locator.evaluate(
		(el, name) => String(getComputedStyle(el)[name]),
		property,
	);
}

const THEMES: Theme[] = ["light", "dark"];

for (const theme of THEMES) {
	const label = theme === "dark" ? "R5 dark:" : "R5";
	test(`${label} the active phase tab differs from an inactive one in background or shadow`, async ({
		page,
	}) => {
		await openPhase(page, theme);
		const active = page.locator('[data-phase-tab][data-state="active"]');
		const inactive = page
			.locator('[data-phase-tab][data-state="inactive"]')
			.first();
		await expect(active).toHaveCount(1);
		const activeBackground = await computed(active, "backgroundColor");
		const inactiveBackground = await computed(inactive, "backgroundColor");
		const activeShadow = await computed(active, "boxShadow");
		const inactiveShadow = await computed(inactive, "boxShadow");
		expect(
			activeBackground !== inactiveBackground ||
				activeShadow !== inactiveShadow,
		).toBe(true);
	});
}

for (const theme of THEMES) {
	const label = theme === "dark" ? "R6 dark:" : "R6";
	test(`${label} phase tab labels render with a capital first letter`, async ({
		page,
	}) => {
		await openPhase(page, theme);
		const labels = await page.locator("[data-phase-tab]").allInnerTexts();
		expect(labels.length).toBeGreaterThan(1);
		for (const text of labels) {
			const first = text.charAt(0);
			expect(first).toBe(first.toUpperCase());
			expect(first).not.toBe(first.toLowerCase());
		}
	});
}

for (const theme of THEMES) {
	const label = theme === "dark" ? "R7 dark:" : "R7";
	test(`${label} adjacent phase tab triggers are at least 4px apart`, async ({
		page,
	}) => {
		await openPhase(page, theme);
		const first = await page.locator("[data-phase-tab]").nth(0).boundingBox();
		const second = await page.locator("[data-phase-tab]").nth(1).boundingBox();
		if (!first || !second)
			throw new Error("phase tab bounding boxes are missing");
		expect(second.x - (first.x + first.width)).toBeGreaterThanOrEqual(4);
	});
}
