/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const HOME = "/#/";
const AREA = "/#/area/e2e-area";
const EFFORT = "/#/effort/e2e-alpha";
const PHASES = ["e2e-phase", "e2e-chain", "e2e-wide", "e2e-done"].map(
	(phase) => `/#/phase/e2e-alpha/${phase}`,
);
const JOURNAL = "/#/journal/e2e-alpha";

test.use({ viewport: { width: 420, height: 800 } });

async function open(page: Page, url: string) {
	await page.goto(url);
	await page.waitForSelector(".main > *");
	await page.waitForLoadState("networkidle");
}

const overflow = (page: Page) =>
	page.evaluate(() => {
		const root = document.documentElement;
		return { scrollWidth: root.scrollWidth, clientWidth: root.clientWidth };
	});

async function expectNoScroll(page: Page, url: string) {
	await open(page, url);
	const { scrollWidth, clientWidth } = await overflow(page);
	expect(scrollWidth, url).toBeLessThanOrEqual(clientWidth);
}

test("R21 the product home screen does not scroll horizontally at 420px", async ({
	page,
}) => {
	await expectNoScroll(page, HOME);
});

test("R22 the area page does not scroll horizontally at 420px", async ({
	page,
}) => {
	await expectNoScroll(page, AREA);
});

test("R23 the effort page does not scroll horizontally at 420px", async ({
	page,
}) => {
	await expectNoScroll(page, EFFORT);
});

test("R24 the phase page does not scroll horizontally at 420px", async ({
	page,
}) => {
	for (const url of PHASES) await expectNoScroll(page, url);
});

test("R25 the journal page does not scroll horizontally at 420px", async ({
	page,
}) => {
	await expectNoScroll(page, JOURNAL);
});

test("R26 the theme switch lies fully inside the viewport at 420px", async ({
	page,
}) => {
	for (const url of [HOME, EFFORT, PHASES[0], PHASES[2]]) {
		await open(page, url);
		const box = await page.locator(".theme-switch").boundingBox();
		expect(box, url).not.toBeNull();
		expect(box?.x, url).toBeGreaterThanOrEqual(0);
		expect((box?.x ?? 0) + (box?.width ?? 0), url).toBeLessThanOrEqual(420);
	}
});

test("R27 the breadcrumb shows the current page label at 420px", async ({
	page,
}) => {
	for (const url of [AREA, EFFORT, PHASES[0], PHASES[2], JOURNAL]) {
		await open(page, url);
		const current = page.locator("[data-breadcrumb] [aria-current='page']");
		await expect(current, url).toBeVisible();
		const fit = await page.evaluate(() => {
			const label = document.querySelector(
				"[data-breadcrumb] [aria-current='page']",
			) as HTMLElement;
			const crumbs = document.querySelector(".crumbs") as HTMLElement;
			const box = label.getBoundingClientRect();
			const bounds = crumbs.getBoundingClientRect();
			return {
				clipped: label.scrollWidth > label.clientWidth,
				left: box.left >= bounds.left - 0.5,
				right: box.right <= bounds.right + 0.5,
			};
		});
		expect(fit, url).toEqual({ clipped: false, left: true, right: true });
	}
});

async function expectToggleLabel(page: Page, url: string) {
	await open(page, url);
	const label = page.locator("label.rail-toggle-label");
	await expect(label).toBeVisible();
	await label.scrollIntoViewIfNeeded();
	await expect(label).toBeInViewport();
}

test("R28 the rail toggle label is visible on the phase page at 420px", async ({
	page,
}) => {
	await expectToggleLabel(page, PHASES[0]);
});

test("R29 the rail toggle label is visible on the effort page at 420px", async ({
	page,
}) => {
	await expectToggleLabel(page, EFFORT);
});

test("R30 a click on the rail toggle label makes the rail visible at 420px", async ({
	page,
}) => {
	await open(page, PHASES[0]);
	await expect(page.locator(".rail")).toBeHidden();
	await page.locator("label.rail-toggle-label").click();
	await expect(page.locator(".rail")).toBeVisible();
});
