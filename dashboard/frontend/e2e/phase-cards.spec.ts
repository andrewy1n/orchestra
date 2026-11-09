/// <reference lib="dom" />
import { type ChildProcess, spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { expect, type Page, test } from "@playwright/test";

const SEED_SERVER = `
import sys
sys.path.insert(0, "e2e")
import json, subprocess
import serve

original = serve.seed

def seed(store_root, env):
    original(store_root, env)
    canon = [sys.executable, "-m", "orchestra.canon", "--root", str(store_root)]

    def update(record_type, subject, *states):
        for state in states:
            serve.run(
                [*canon, "update", "--type", record_type, "--subject", subject, "--transition", state],
                serve.REPO_ROOT,
                env,
            )

    for phase in (serve.PHASE, serve.CHAIN_PHASE, serve.WIDE_PHASE):
        update("score:phase", phase, "in_progress")
    update("score:work-item", serve.TASK, "in_progress", "done")
    update("score:work-item", serve.CHAIN_PHASE + "-1", "in_progress")

serve.seed = seed
sys.argv = ["serve", "--port", sys.argv[1]]
sys.exit(serve.main())
`;

const TITLES = ["E2E phase", "E2E chain phase", "E2E wide phase"];

let server: ChildProcess;
let origin = "";

test.beforeAll(async () => {
	const port = String(41000 + Math.floor(Math.random() * 2000));
	server = spawn("uv", ["run", "python", "-c", SEED_SERVER, port], {
		cwd: process.cwd(),
		stdio: ["ignore", "pipe", "inherit"],
	});
	const lines = createInterface({
		input: server.stdout as NodeJS.ReadableStream,
	});
	origin = await new Promise<string>((resolve, reject) => {
		server.once("exit", () => reject(new Error("seeded server exited early")));
		lines.on("line", (line) => {
			if (line.startsWith("http://")) resolve(line.trim());
		});
	});
	await expect
		.poll(
			async () => {
				try {
					return (await fetch(`${origin}/api/hub`)).status;
				} catch {
					return 0;
				}
			},
			{ timeout: 60_000 },
		)
		.toBe(200);
});

test.afterAll(async () => {
	if (!server || server.exitCode !== null) return;
	const exited = new Promise((resolve) => server.once("exit", resolve));
	server.kill("SIGTERM");
	await exited;
});

async function openWork(page: Page, theme = "light") {
	await page.addInitScript((stored) => {
		window.localStorage.setItem("theme", stored);
	}, theme);
	await page.goto(`${origin}/#/`);
	await expect(
		page.locator("[data-hub] [data-phase-card]").first(),
	).toBeVisible();
}

test("R2 the Work screen shows one card per in-progress phase with the running phase first", async ({
	page,
}) => {
	await openWork(page);
	const cards = page.locator("[data-hub] [data-phase-card]");
	await expect(cards).toHaveCount(3);
	const titles = await cards.locator("[data-title]").allTextContents();
	expect([...titles].sort()).toEqual([...TITLES].sort());
	expect(titles[0]).toBe("E2E chain phase");
	await expect(cards.first().locator("[data-running]")).toBeVisible();

	const firstSection = await page.evaluate(() => {
		const hub = document.querySelector("[data-hub]");
		const first = hub?.querySelector(
			"[data-active-phases], [data-hub-row], [data-panel]",
		);
		return first?.hasAttribute("data-active-phases") ?? false;
	});
	expect(firstSection).toBe(true);

	const next = page.locator("[data-work-next]");
	await expect(next).toBeVisible();
	const nextText = (await next.textContent()) ?? "";
	for (const title of TITLES) expect(nextText).not.toContain(title);
});

const MODES = ["light", "dark"] as const;
const WIDTHS = [420, 1280] as const;

for (const theme of MODES) {
	for (const width of WIDTHS) {
		test(`R16 the cards stay readable at ${width}px in the ${theme} scheme`, async ({
			page,
		}) => {
			await page.setViewportSize({ width, height: 900 });
			await openWork(page, theme);
			await page.waitForLoadState("networkidle");
			await expect(page.locator("html")).toHaveAttribute("data-theme", theme);

			const overflow = await page.evaluate(() => ({
				scroll: document.documentElement.scrollWidth,
				inner: window.innerWidth,
			}));
			expect(overflow.scroll).toBeLessThanOrEqual(overflow.inner);

			const stages = page.locator("[data-phase-card] [data-stage]");
			const count = await stages.count();
			expect(count).toBeGreaterThanOrEqual(3 * 4);
			for (let i = 0; i < count; i++) {
				const stage = stages.nth(i);
				await expect(stage).toBeVisible();
				const box = await stage.boundingBox();
				expect(box?.width ?? 0).toBeGreaterThan(0);
			}

			const clipped = await page.evaluate(() =>
				[...document.querySelectorAll<HTMLElement>("[data-stage]")]
					.filter((el) => el.scrollWidth > el.clientWidth)
					.map(
						(el) => `${el.dataset.stage}:${el.scrollWidth}>${el.clientWidth}`,
					),
			);
			expect(clipped, "clipped stepper labels").toEqual([]);

			const ratios = await page.evaluate(() => {
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
				const backdrop = (el: Element): number[] => {
					let layers: [number, number, number, number][] = [];
					for (let node: Element | null = el; node; node = node.parentElement) {
						const bg = toRgba(getComputedStyle(node).backgroundColor);
						if (bg[3] > 0) layers.push(bg);
						if (bg[3] === 1) break;
					}
					layers = layers.reverse();
					let base: number[] = [255, 255, 255];
					for (const layer of layers)
						base = base.map((v, i) => layer[i] * layer[3] + v * (1 - layer[3]));
					return base;
				};
				const selectors = [
					"[data-title]",
					"[data-effort]",
					"[data-reason]",
					"[data-stage]",
					".pc-name",
					".pc-label",
					"[data-gate]",
				];
				const out: { selector: string; ratio: number }[] = [];
				for (const card of document.querySelectorAll("[data-phase-card]")) {
					for (const selector of selectors) {
						for (const el of card.querySelectorAll(selector)) {
							const fg = toRgba(getComputedStyle(el).color);
							const bg = backdrop(el);
							const blended = fg
								.slice(0, 3)
								.map((v, i) => v * fg[3] + bg[i] * (1 - fg[3]));
							const a = luminance(blended);
							const b = luminance(bg);
							out.push({
								selector,
								ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
							});
						}
					}
				}
				return out;
			});
			expect(ratios.length).toBeGreaterThan(0);
			for (const { selector, ratio } of ratios)
				expect(ratio, `${selector} contrast`).toBeGreaterThanOrEqual(4.5);
		});
	}
}
