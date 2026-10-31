/// <reference lib="dom" />
import { expect, type Page, test } from "@playwright/test";

const EFFORT_URL = "/#/effort/e2e-alpha";

type SnapshotBody = {
	efforts: Array<{
		effort: string;
		needs_you: unknown[];
		backlog: Array<Record<string, string>>;
	}>;
};

async function patchSnapshot(
	page: Page,
	mutate: (effort: SnapshotBody["efforts"][number]) => void,
) {
	await page.route("**/api/snapshot", async (route) => {
		const response = await route.fetch();
		const body = (await response.json()) as SnapshotBody;
		mutate(
			body.efforts.find((row) => row.effort === "e2e-alpha") ?? body.efforts[0],
		);
		await route.fulfill({ response, json: body });
	});
}

const withEmptyNeeds = (effort: SnapshotBody["efforts"][number]) => {
	effort.needs_you = [];
};

const withBacklogItem = (effort: SnapshotBody["efforts"][number]) => {
	effort.backlog = [
		{
			id: "rec-side-idea",
			subject: "side-idea",
			effort: "e2e-alpha",
			text: "Park the side idea",
			status: "open",
			source: "",
			phase: "",
			body: "Park the side idea",
			record_type: "composer:idea",
		},
	];
};

const fontSize = (page: Page, selector: string) =>
	page
		.locator(selector)
		.first()
		.evaluate((el) => Number.parseFloat(getComputedStyle(el).fontSize));

const tokenColour = (page: Page, token: string) =>
	page.evaluate((name) => {
		const probe = document.createElement("span");
		probe.style.backgroundColor = `var(${name})`;
		document.body.append(probe);
		const colour = getComputedStyle(probe).backgroundColor;
		probe.remove();
		return colour;
	}, token);

test("R16 the right panel section titles render at 14px", async ({ page }) => {
	await patchSnapshot(page, (effort) => {
		withEmptyNeeds(effort);
		withBacklogItem(effort);
	});
	await page.goto(EFFORT_URL);
	const titles = page.locator(".side h2");
	await expect(titles).toHaveCount(2);
	await expect(titles.nth(0)).toContainText("Needs you");
	await expect(titles.nth(1)).toContainText("Backlog");
	await expect(titles.nth(0)).toHaveCSS("font-size", "14px");
	await expect(titles.nth(1)).toHaveCSS("font-size", "14px");
});

test("R17 the right panel record ids render at 12px", async ({ page }) => {
	await patchSnapshot(page, withBacklogItem);
	await page.goto(EFFORT_URL);
	const ids = page.locator("[data-side-backlog] [data-record-id]");
	await expect(ids).toHaveCount(1);
	await expect(ids.first()).toHaveText("side-idea");
	await expect(ids.first()).toHaveCSS("font-size", "12px");
});

test("R18 the right panel empty-state text is no larger than the section title", async ({
	page,
}) => {
	await patchSnapshot(page, withEmptyNeeds);
	await page.goto(EFFORT_URL);
	await expect(page.locator(".side")).toContainText("Nothing needs you");
	await expect(page.locator(".side")).toContainText("No backlog");
	const title = await fontSize(page, ".side h2");
	for (const text of ["Nothing needs you", "No backlog"]) {
		const empty = await fontSize(page, `.side p:text-is("${text}")`);
		expect(empty).toBeLessThanOrEqual(title);
		expect(empty).toBe(12);
	}
});

test("R19 the footer shows a green dot beside Live when polling succeeds", async ({
	page,
}) => {
	await page.goto(EFFORT_URL);
	const footer = page.locator("footer");
	await expect(footer).toContainText("Live");
	const dot = footer.locator("[data-status-dot]");
	await expect(dot).toBeVisible();
	await expect(dot).toHaveCSS(
		"background-color",
		await tokenColour(page, "--done"),
	);
	const dotBox = await dot.boundingBox();
	const textBox = await footer.locator("[data-status-text]").boundingBox();
	expect(dotBox).not.toBeNull();
	expect(textBox).not.toBeNull();
	if (!dotBox || !textBox) return;
	expect(dotBox.x + dotBox.width).toBeLessThanOrEqual(textBox.x + 1);
	expect(textBox.x - (dotBox.x + dotBox.width)).toBeLessThanOrEqual(16);
	expect(
		Math.abs(dotBox.y + dotBox.height / 2 - (textBox.y + textBox.height / 2)),
	).toBeLessThanOrEqual(4);
	await expect(footer.locator("[data-status-text]")).toHaveCSS(
		"font-size",
		"12px",
	);
});

test("R20 the footer shows a red dot beside the error text when polling fails", async ({
	page,
}) => {
	await page.goto(EFFORT_URL);
	await expect(page.locator("footer")).toContainText("Live");
	await page.route("**/api/token", (route) =>
		route.fulfill({ json: { token: "changed-token" } }),
	);
	await page.route("**/api/snapshot", (route) =>
		route.fulfill({ status: 500, body: "boom" }),
	);
	const footer = page.locator("footer");
	await expect(footer).toContainText("failed: 500", { timeout: 10_000 });
	await expect(footer).not.toContainText("Live");
	const dot = footer.locator("[data-status-dot]");
	await expect(dot).toBeVisible();
	await expect(dot).toHaveCSS(
		"background-color",
		await tokenColour(page, "--fail"),
	);
	const dotBox = await dot.boundingBox();
	const textBox = await footer.locator("[data-status-text]").boundingBox();
	expect(dotBox).not.toBeNull();
	expect(textBox).not.toBeNull();
	if (!dotBox || !textBox) return;
	expect(dotBox.x + dotBox.width).toBeLessThanOrEqual(textBox.x + 1);
});
