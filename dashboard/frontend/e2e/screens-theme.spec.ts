/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const ROUTE = "/#/phase/e2e-alpha/e2e-phase";

async function seedTheme(page: Page, value: string) {
	await page.addInitScript((stored) => {
		window.localStorage.setItem("theme", stored);
	}, value);
}

const rootTheme = (page: Page) =>
	page.evaluate(() => ({
		dataTheme: document.documentElement.dataset.theme,
		dark: document.documentElement.classList.contains("dark"),
	}));

test("R1 the theme switch stores the chosen theme under the localStorage key theme", async ({
	page,
}) => {
	await page.goto(ROUTE);
	await page.locator(".theme-switch").click();
	await expect(page.locator(".theme-switch")).toHaveAttribute(
		"aria-checked",
		"true",
	);
	expect(await page.evaluate(() => window.localStorage.getItem("theme"))).toBe(
		"dark",
	);
	await page.locator(".theme-switch").click();
	expect(await page.evaluate(() => window.localStorage.getItem("theme"))).toBe(
		"light",
	);
});

test("R2 a load with theme dark in localStorage renders the dark theme", async ({
	page,
}) => {
	await seedTheme(page, "dark");
	await page.goto(ROUTE);
	await page.reload();
	await expect(page.locator(".theme-switch")).toHaveAttribute(
		"aria-checked",
		"true",
	);
	expect(await rootTheme(page)).toEqual({ dataTheme: "dark", dark: true });
});

test("R3 a load with no stored theme renders the light theme", async ({
	page,
}) => {
	await page.goto(ROUTE);
	await page.reload();
	await expect(page.locator(".theme-switch")).toHaveAttribute(
		"aria-checked",
		"false",
	);
	expect(await rootTheme(page)).toEqual({ dataTheme: "light", dark: false });
	expect(
		await page.evaluate(() => window.localStorage.getItem("theme")),
	).toBeNull();
});

test("R4 a load with an unknown stored theme renders the light theme", async ({
	page,
}) => {
	await seedTheme(page, "solarized");
	await page.goto(ROUTE);
	await page.reload();
	await expect(page.locator(".theme-switch")).toHaveAttribute(
		"aria-checked",
		"false",
	);
	expect(await rootTheme(page)).toEqual({ dataTheme: "light", dark: false });
});
