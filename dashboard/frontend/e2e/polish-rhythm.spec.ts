/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";

const BLOCKS = [
	["title row", "[data-phase-title]"],
	["phase tabs", "[data-phase-tabs]"],
	["chrome box", "[data-phase-chrome]"],
	["graph", "[data-task-graph]"],
	["status tabs", "[data-status-tabs]"],
	["task table", "[data-task-table]"],
	["notes", '[data-detail-section="Phase notes"]'],
] as const;

async function openPhase(page: Page, theme: "light" | "dark") {
	await page.setViewportSize({ width: 1280, height: 900 });
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-state]")).toBeVisible();
	if (theme === "dark") {
		await page.locator(".theme-switch").click();
		await expect(page.locator("html")).toHaveClass(/dark/);
	}
	for (const [, selector] of BLOCKS) {
		await expect(page.locator(selector).first()).toBeVisible();
	}
}

function gaps(page: Page) {
	return page.evaluate(
		(selectors) => {
			const root = document.querySelector("[data-phase-page]");
			if (!root) throw new Error("phase page is missing");
			const rects = selectors.map(([name, selector]) => {
				let el = document.querySelector(selector);
				while (el && el.parentElement !== root) el = el.parentElement;
				if (!el) throw new Error(`${name} is not a block of the phase page`);
				return { name, rect: el.getBoundingClientRect() };
			});
			return rects.slice(1).map((block, index) => {
				const prev = rects[index];
				if (!prev) throw new Error("block order is broken");
				return {
					pair: `${prev.name} -> ${block.name}`,
					gap: block.rect.top - prev.rect.bottom,
				};
			});
		},
		BLOCKS.map((block) => [...block]),
	);
}

for (const theme of ["light", "dark"] as const) {
	test(`R9 the phase page blocks are 16px apart in ${theme} mode`, async ({
		page,
	}) => {
		await openPhase(page, theme);
		const measured = await gaps(page);
		expect(measured).toHaveLength(BLOCKS.length - 1);
		for (const { pair, gap } of measured) {
			expect(gap, pair).toBe(16);
		}
	});
}
