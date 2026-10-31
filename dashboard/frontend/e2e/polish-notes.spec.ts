/// <reference lib="dom" />
import { expect, test } from "@playwright/test";

test("R10 a phase notes section is at most 72ch wide", async ({ page }) => {
	await page.setViewportSize({ width: 1600, height: 900 });
	await page.goto("/#/phase/e2e-alpha/e2e-phase");
	const section = page.locator('[data-detail-section="Phase notes"]');
	await expect(section).toBeVisible();
	const widths = await section.evaluate((el) => {
		const probe = document.createElement("div");
		probe.style.width = "72ch";
		el.appendChild(probe);
		const cap = probe.getBoundingClientRect().width;
		probe.remove();
		return {
			cap,
			section: el.getBoundingClientRect().width,
			container:
				el.closest("[data-phase-page]")?.getBoundingClientRect().width ?? 0,
		};
	});
	expect(widths.container).toBeGreaterThan(widths.cap);
	expect(widths.section).toBeLessThanOrEqual(widths.cap + 0.5);
});
