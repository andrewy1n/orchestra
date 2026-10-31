/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const ROUTES = [
	"/",
	"/#/area/e2e-area",
	"/#/effort/e2e-alpha",
	"/#/phase/e2e-alpha/e2e-phase",
	"/#/journal",
];

const ALLOWED_SIZES = [12, 14, 16, 20];

interface TextElement {
	selector: string;
	size: number;
	text: string;
}

type Theme = "light" | "dark";

const THEMES: Theme[] = ["light", "dark"];

const DARK_CLASS = /(^|\s)dark(\s|$)/;

async function switchToDark(page: Page) {
	await page.locator(".theme-switch").click();
	await expect(page.locator("html")).toHaveClass(DARK_CLASS);
}

async function openRoute(page: Page, url: string) {
	await page.goto(url);
	await page.waitForLoadState("networkidle");
	await expect
		.poll(() => page.locator(".main").textContent(), {
			message: `${url} content`,
		})
		.toMatch(/\S/);
}

function collectTextElements(page: Page): Promise<TextElement[]> {
	return page.evaluate(() => {
		const describe = (el: Element): string => {
			const parts: string[] = [];
			for (
				let node: Element | null = el;
				node && node !== document.documentElement && parts.length < 4;
				node = node.parentElement
			) {
				const id = node.id ? `#${node.id}` : "";
				const cls =
					typeof node.className === "string" && node.className.trim()
						? `.${node.className.trim().split(/\s+/).slice(0, 2).join(".")}`
						: "";
				parts.unshift(`${node.tagName.toLowerCase()}${id}${cls}`);
			}
			return parts.join(" > ");
		};
		const hidden = (el: Element): boolean => {
			if (el.closest(".sr-only")) return true;
			if (el.getClientRects().length === 0) return true;
			const box = el.getBoundingClientRect();
			return box.width <= 1 && box.height <= 1;
		};
		const found: TextElement[] = [];
		for (const el of document.querySelectorAll("*")) {
			if (["SCRIPT", "STYLE", "NOSCRIPT"].includes(el.tagName.toUpperCase()))
				continue;
			const own = [...el.childNodes]
				.filter((node) => node.nodeType === Node.TEXT_NODE)
				.map((node) => node.textContent?.trim() ?? "")
				.join(" ")
				.trim();
			if (!own || hidden(el)) continue;
			found.push({
				selector: describe(el),
				size: Number.parseFloat(getComputedStyle(el).fontSize),
				text: own.slice(0, 40),
			});
		}
		return found;
	});
}

for (const theme of THEMES) {
	const label = theme === "dark" ? "R8 dark:" : "R8";
	test(`${label} body text renders in Inter at 14px by default`, async ({
		page,
	}) => {
		await openRoute(page, "/");
		if (theme === "dark") await switchToDark(page);
		const body = await page.evaluate(() => {
			const style = getComputedStyle(document.body);
			return { family: style.fontFamily, size: style.fontSize };
		});
		expect(body.size).toBe("14px");
		expect(body.family).toMatch(/^"?Inter/);
		const loaded = await page.evaluate(() =>
			document.fonts.ready.then(() =>
				document.fonts.check('14px "Inter Variable"'),
			),
		);
		expect(loaded).toBe(true);
	});
}

for (const theme of THEMES) {
	const label = theme === "dark" ? "R9 dark:" : "R9";
	test(`${label} every text element on the main screens uses 12, 14, 16 or 20px`, async ({
		page,
	}) => {
		const offenders: string[] = [];
		for (const [index, url] of ROUTES.entries()) {
			await openRoute(page, url);
			if (theme === "dark") {
				if (index === 0) await switchToDark(page);
				await expect(page.locator("html")).toHaveClass(DARK_CLASS);
			}
			const elements = await collectTextElements(page);
			expect(elements.length, `${url} has text`).toBeGreaterThan(0);
			for (const element of elements) {
				if (!ALLOWED_SIZES.includes(element.size)) {
					offenders.push(
						`${url}  ${element.size}px  ${element.selector}  "${element.text}"`,
					);
				}
			}
		}
		expect(
			offenders,
			`text outside ${ALLOWED_SIZES.join("/")}px:\n${offenders.join("\n")}`,
		).toEqual([]);
	});
}
