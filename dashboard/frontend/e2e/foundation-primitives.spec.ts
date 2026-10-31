/// <reference lib="dom" />
import { expect, type Locator, type Page, test } from "@playwright/test";

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

interface PhasePayload {
	detail: Record<string, unknown>;
}

async function openPhaseWith(
	page: Page,
	patch: (detail: Record<string, unknown>) => void,
) {
	await page.route("**/api/phase?*", async (route) => {
		const response = await route.fetch();
		const payload = (await response.json()) as PhasePayload;
		patch(payload.detail);
		await route.fulfill({ response, json: payload });
	});
	await page.goto(PHASE_URL);
}

function backgroundOf(locator: Locator) {
	return locator.evaluate((el) => getComputedStyle(el).backgroundColor);
}

function tokenBackground(page: Page, token: string) {
	return page.evaluate((name) => {
		const probe = document.createElement("div");
		probe.style.backgroundColor = `var(${name})`;
		document.body.append(probe);
		const colour = getComputedStyle(probe).backgroundColor;
		probe.remove();
		return colour;
	}, token);
}

const BADGE_VARIANTS = [
	{ variant: "default", state: "in_progress", utility: "bg-primary" },
	{ variant: "secondary", state: "done", utility: "bg-secondary" },
] as const;

for (const { variant, state, utility } of BADGE_VARIANTS) {
	test(`R2 a shadcn badge of the ${variant} variant keeps its background colour`, async ({
		page,
	}) => {
		await openPhaseWith(page, (detail) => {
			detail.state = state;
		});
		const badge = page.locator(`[data-slot=badge].${utility}`);
		await expect(badge).toHaveCount(1);
		const expected = await tokenBackground(page, `--${utility.slice(3)}`);
		expect(expected).not.toBe("rgba(0, 0, 0, 0)");
		expect(await backgroundOf(badge)).toBe(expected);
	});
}

test("R2 a shadcn button of the outline variant keeps its background colour", async ({
	page,
}) => {
	await openPhaseWith(page, (detail) => {
		detail.evidence = {
			requirements: [
				{ id: "R-probe", text: "probe", latest_check: { result: "pass" } },
			],
		};
	});
	const button = page.locator("[data-slot=button].bg-background").first();
	await expect(button).toBeVisible();
	const expected = await tokenBackground(page, "--background");
	expect(expected).not.toBe("rgba(0, 0, 0, 0)");
	expect(await backgroundOf(button)).toBe(expected);
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
