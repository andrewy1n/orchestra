/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const PHASE_URL = "/#/phase/e2e-alpha/e2e-phase";

const ALIASES: Record<string, string> = {
	"--ink": "--foreground",
	"--ink-2": "--foreground",
	"--text-muted": "--muted-foreground",
	"--faint": "--muted-foreground",
	"--line": "--border",
	"--line-2": "--border",
	"--panel": "--card",
	"--bg": "--background",
	"--sunken": "--muted",
};

async function openPhase(page: Page, theme: "light" | "dark") {
	await page.goto(PHASE_URL);
	await expect(page.locator("[data-phase-state]")).toBeVisible();
	if (theme === "dark") {
		await page.locator(".theme-switch").click();
		await expect(page.locator("html")).toHaveClass(/dark/);
	}
}

function phaseStateContrast(page: Page) {
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
		const label = document.querySelector("[data-phase-state]");
		if (!label) throw new Error("phase state label is missing");
		const foreground = toRgba(getComputedStyle(label).color);
		const background = toRgba(getComputedStyle(document.body).backgroundColor);
		const blended = foreground
			.slice(0, 3)
			.map((v, i) => v * foreground[3] + background[i] * (1 - foreground[3]));
		const a = luminance(blended);
		const b = luminance(background);
		return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
	});
}

async function aliasValues(page: Page) {
	return page.evaluate((aliases) => {
		const style = getComputedStyle(document.documentElement);
		return Object.entries(aliases).map(([name, token]) => ({
			name,
			token,
			value: style.getPropertyValue(name).trim(),
			tokenValue: style.getPropertyValue(token).trim(),
		}));
	}, ALIASES);
}

test("R3 the phase state label has at least 4.5:1 contrast in light mode", async ({
	page,
}) => {
	await openPhase(page, "light");
	expect(await phaseStateContrast(page)).toBeGreaterThanOrEqual(4.5);
});

test("R4 the phase state label has at least 4.5:1 contrast in dark mode", async ({
	page,
}) => {
	await openPhase(page, "dark");
	expect(await phaseStateContrast(page)).toBeGreaterThanOrEqual(4.5);
});

test("R12 each old colour name equals its shadcn token in light mode", async ({
	page,
}) => {
	await openPhase(page, "light");
	for (const { name, tokenValue, value } of await aliasValues(page)) {
		expect(tokenValue, `${name} token is defined`).not.toBe("");
		expect(value, name).toBe(tokenValue);
	}
});

test("R13 each old colour name equals its shadcn token in dark mode", async ({
	page,
}) => {
	await openPhase(page, "dark");
	for (const { name, tokenValue, value } of await aliasValues(page)) {
		expect(tokenValue, `${name} token is defined`).not.toBe("");
		expect(value, name).toBe(tokenValue);
	}
});
