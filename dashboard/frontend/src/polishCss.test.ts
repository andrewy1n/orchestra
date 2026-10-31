import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const e2eDir = path.join(srcDir, "..", "e2e");
const cssPath = path.join(srcDir, "app.css");

const DEAD_SELECTORS = [
	".phase-chrome",
	".phase-next",
	".phase-reqs",
	".evidence-req",
	".evidence-reqs",
	".section-card",
	".rail-item",
];

const SOURCE_EXTENSIONS = [".svelte", ".ts", ".css"];

function sourceFiles(dir: string): string[] {
	return readdirSync(dir, { recursive: true, withFileTypes: true })
		.filter(
			(entry) =>
				entry.isFile() &&
				SOURCE_EXTENSIONS.some((ext) => entry.name.endsWith(ext)),
		)
		.map((entry) => path.join(entry.parentPath, entry.name))
		.sort();
}

function stripCssComments(text: string): string {
	return text.replace(/\/\*[\s\S]*?\*\//g, "");
}

function escapeRegExp(text: string): string {
	return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

describe("phase page polish css", () => {
	const css = stripCssComments(readFileSync(cssPath, "utf8"));

	it("R19 app.css defines none of the dead phase page selectors", () => {
		const defined = DEAD_SELECTORS.filter((selector) =>
			new RegExp(`${escapeRegExp(selector)}(?![\\w-])`).test(css),
		);
		expect(defined).toEqual([]);
	});

	it("R20 every colour alias in app.css is referenced by a source file", () => {
		const root = /:root\s*\{([\s\S]*?)\n\}/.exec(css)?.[1] ?? "";
		const aliases = [...root.matchAll(/^\s*(--[\w-]+):\s*var\(--[\w-]+\);/gm)]
			.map((match) => match[1])
			.filter((name): name is string => name !== undefined);
		expect(aliases.length).toBeGreaterThan(0);

		const definition = (name: string) =>
			new RegExp(
				`^\\s*${escapeRegExp(name)}:\\s*var\\(--[\\w-]+\\);\\s*$`,
				"gm",
			);
		const files = [...sourceFiles(srcDir), ...sourceFiles(e2eDir)].map(
			(file) => ({
				file,
				text: stripCssComments(readFileSync(file, "utf8")),
			}),
		);

		const unused = aliases.filter((name) => {
			const reference = new RegExp(`${escapeRegExp(name)}(?![\\w-])`);
			return !files.some(({ file, text }) => {
				const body =
					file === cssPath ? text.replace(definition(name), "") : text;
				return reference.test(body);
			});
		});
		expect(unused).toEqual([]);
	});
});
