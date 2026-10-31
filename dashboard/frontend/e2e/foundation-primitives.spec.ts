import { expect, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";

test("R1 a shadcn tab trigger renders at a font size of 14px", async ({
	page,
}) => {
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-tab]").first()).toHaveCSS(
		"font-size",
		"14px",
	);
});

test("R2 a shadcn badge keeps the background colour of its variant class", async ({
	page,
}) => {
	await page.goto(PHASE_URL);
	const badge = page.locator("[data-slot=badge]").first();
	await expect(badge).toBeVisible();
	const { actual, expected } = await badge.evaluate((el) => {
		const doc = el.ownerDocument;
		const view = doc.defaultView;
		if (!view) throw new Error("no window");
		const button = doc.createElement("button");
		button.className = `${el.className} bg-primary`;
		doc.body.append(button);
		const probe = doc.createElement("div");
		probe.style.backgroundColor = "var(--color-primary)";
		doc.body.append(probe);
		const result = {
			actual: view.getComputedStyle(button).backgroundColor,
			expected: view.getComputedStyle(probe).backgroundColor,
		};
		button.remove();
		probe.remove();
		return result;
	});
	expect(expected).not.toBe("rgba(0, 0, 0, 0)");
	expect(actual).toBe(expected);
});

test("R22 a shadcn tab trigger renders at a font weight of 500", async ({
	page,
}) => {
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-tab]").first()).toHaveCSS(
		"font-weight",
		"500",
	);
});

test("R23 a shadcn tab trigger has a horizontal padding of 8px", async ({
	page,
}) => {
	await page.goto(PHASE_URL);
	const trigger = page.locator("[data-phase-tab]").first();
	await expect(trigger).toHaveCSS("padding-left", "8px");
	await expect(trigger).toHaveCSS("padding-right", "8px");
});
