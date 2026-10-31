/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";
const MIN_CONTRAST = 3;
const MAX_STEPS = 80;

type Theme = "light" | "dark";

interface Indicator {
	kind: "outline" | "box-shadow";
	css: string;
	contrast: number;
}

interface FocusReading {
	outline: string;
	outlineOffset: string;
	boxShadow: string;
	indicators: Indicator[];
	best: number;
}

interface PhasePayload {
	detail: Record<string, unknown>;
}

const TARGETS = {
	"phase tab": "[data-phase-tab]",
	"status tab": "[data-status-tabs] [data-slot=tabs-trigger]",
	"requirement chip": "[data-phase-req]",
	"task row": "[data-task]",
} as const;

async function openPhase(page: Page, theme: Theme) {
	await page.route("**/api/phase?*", async (route) => {
		const response = await route.fetch();
		const payload = (await response.json()) as PhasePayload;
		payload.detail.evidence = {
			requirements: [
				{ id: "R-probe", text: "probe", latest_check: { result: "pass" } },
			],
		};
		await route.fulfill({ response, json: payload });
	});
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-req]").first()).toBeVisible();
	await expect(page.locator("[data-task]").first()).toBeVisible();
	if (theme === "dark") {
		await page.locator(".theme-switch").click();
		await expect(page.locator("html")).toHaveClass(/(^|\s)dark(\s|$)/);
	}
	await page.evaluate(() => {
		(document.activeElement as HTMLElement | null)?.blur();
	});
}

function isFocused(page: Page, selector: string) {
	return page.evaluate(
		(sel) => document.activeElement?.matches(sel) ?? false,
		selector,
	);
}

async function focusByKeys(page: Page, selector: string) {
	for (const key of ["Tab", "Shift+Tab"]) {
		for (let step = 0; step < MAX_STEPS; step++) {
			if (await isFocused(page, selector)) return;
			await page.keyboard.press(key);
		}
	}
	throw new Error(`keyboard never reached ${selector}`);
}

async function readFocus(page: Page): Promise<FocusReading> {
	await page.evaluate(() =>
		Promise.all(
			document.getAnimations().map((animation) => animation.finished),
		),
	);
	return page.evaluate(() => {
		const toRgba = (css: string): [number, number, number, number] => {
			const canvas = document.createElement("canvas");
			canvas.width = 1;
			canvas.height = 1;
			const ctx = canvas.getContext("2d", { willReadFrequently: true });
			if (!ctx) throw new Error("canvas context is missing");
			ctx.clearRect(0, 0, 1, 1);
			ctx.fillStyle = css;
			ctx.fillRect(0, 0, 1, 1);
			const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
			return [r, g, b, a / 255];
		};
		const luminance = ([r, g, b]: number[]) => {
			const lin = (v: number) => {
				const c = v / 255;
				return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
			};
			return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
		};
		const background = toRgba(getComputedStyle(document.body).backgroundColor);
		const contrast = (css: string) => {
			const rgba = toRgba(css);
			if (rgba[3] === 0) return 0;
			const blended = rgba
				.slice(0, 3)
				.map((v, i) => v * rgba[3] + background[i] * (1 - rgba[3]));
			const a = luminance(blended);
			const b = luminance(background);
			return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
		};
		const el = document.activeElement;
		if (!el) throw new Error("nothing is focused");
		const style = getComputedStyle(el);
		const indicators: Indicator[] = [];
		const outlineWidth = Number.parseFloat(style.outlineWidth);
		if (style.outlineStyle !== "none" && outlineWidth > 0) {
			indicators.push({
				kind: "outline",
				css: style.outlineColor,
				contrast: contrast(style.outlineColor),
			});
		}
		const shadows = style.boxShadow
			.split(/,(?![^(]*\))/)
			.map((part) => part.trim())
			.filter((part) => part !== "" && part !== "none");
		for (const shadow of shadows) {
			const lengths = shadow.match(/-?[\d.]+px/g) ?? [];
			const spread = Number.parseFloat(lengths[3] ?? "0");
			if (spread <= 0) continue;
			const colour = shadow
				.replace(/inset/, "")
				.replace(/-?[\d.]+px/g, "")
				.trim();
			indicators.push({
				kind: "box-shadow",
				css: colour,
				contrast: contrast(colour),
			});
		}
		return {
			outline: style.outline,
			outlineOffset: style.outlineOffset,
			boxShadow: style.boxShadow,
			indicators,
			best: Math.max(0, ...indicators.map((item) => item.contrast)),
		};
	});
}

async function expectFocusContrast(theme: Theme, page: Page) {
	await openPhase(page, theme);
	for (const [name, selector] of Object.entries(TARGETS)) {
		await focusByKeys(page, selector);
		const reading = await readFocus(page);
		expect(
			reading.best,
			`${name}: ${JSON.stringify(reading.indicators)}`,
		).toBeGreaterThanOrEqual(MIN_CONTRAST);
	}
}

test("R27 a keyboard-focused phase tab, status tab, requirement chip and task row show an indicator of at least 3:1 in light mode", async ({
	page,
}) => {
	await expectFocusContrast("light", page);
});

test("R28 a keyboard-focused phase tab, status tab, requirement chip and task row show an indicator of at least 3:1 in dark mode", async ({
	page,
}) => {
	await expectFocusContrast("dark", page);
});

test("R29 a keyboard-focused task row shows an outline inside the table container", async ({
	page,
}) => {
	await openPhase(page, "light");
	await focusByKeys(page, TARGETS["task row"]);
	const reading = await readFocus(page);
	expect(reading.outline).not.toMatch(/\bnone\b/);
	expect(
		reading.indicators.some((item) => item.kind === "outline"),
		JSON.stringify(reading),
	).toBe(true);
	const clipped = await page.evaluate(() => {
		const row = document.activeElement;
		const container = row?.closest("table")?.parentElement;
		if (!row || !container) throw new Error("task row or container is missing");
		const style = getComputedStyle(row);
		const reach =
			Number.parseFloat(style.outlineWidth) +
			Number.parseFloat(style.outlineOffset);
		const outer = row.getBoundingClientRect();
		const clip = container.getBoundingClientRect();
		const border = Number.parseFloat(getComputedStyle(container).borderWidth);
		const slack = 0.5;
		return (
			outer.left - reach < clip.left + border - slack ||
			outer.right + reach > clip.right - border + slack ||
			outer.top - reach < clip.top + border - slack ||
			outer.bottom + reach > clip.bottom - border + slack
		);
	});
	expect(clipped, "outline reaches outside the table container").toBe(false);
});
