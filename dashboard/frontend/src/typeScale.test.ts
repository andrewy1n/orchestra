import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const cssPath = path.join(srcDir, "app.css");

const TYPE_TOKENS = ["xs", "sm", "base", "xl"] as const;
const ALLOWED_SIZE = new RegExp(
	`^(inherit|var\\(--text-(${TYPE_TOKENS.join("|")})\\))$`,
);

interface Hit {
	file: string;
	line: number;
	text: string;
}

function svelteFiles(dir: string): string[] {
	return readdirSync(dir, { recursive: true, withFileTypes: true })
		.filter((entry) => entry.isFile() && entry.name.endsWith(".svelte"))
		.map((entry) => path.join(entry.parentPath, entry.name))
		.sort();
}

function sources(): { file: string; text: string }[] {
	return [cssPath, ...svelteFiles(srcDir)].map((file) => ({
		file: path.relative(srcDir, file),
		text: readFileSync(file, "utf8"),
	}));
}

function stripCssComments(text: string): string {
	return text.replace(/\/\*[\s\S]*?\*\//g, (comment) =>
		comment.replace(/[^\n]/g, " "),
	);
}

function lineOf(text: string, index: number): number {
	return text.slice(0, index).split("\n").length;
}

function scan(
	pattern: RegExp,
	accept: (match: RegExpExecArray) => boolean,
): Hit[] {
	const hits: Hit[] = [];
	for (const { file, text } of sources()) {
		const body = file.endsWith(".css") ? stripCssComments(text) : text;
		for (const match of body.matchAll(pattern)) {
			if (accept(match)) continue;
			hits.push({
				file,
				line: lineOf(body, match.index),
				text: match[0].trim(),
			});
		}
	}
	return hits;
}

function report(hits: Hit[]): string {
	return hits.map((hit) => `${hit.file}:${hit.line} ${hit.text}`).join("\n");
}

describe("type scale source scan", () => {
	it("R10 every font-size declaration is a type token or inherit", () => {
		const hits = scan(/(?<![\w-])font-size\s*:\s*([^;}"'\n]+)/g, (match) =>
			ALLOWED_SIZE.test(match[1].trim()),
		);
		expect(report(hits)).toBe("");
	});

	it("R10 no markup attribute sets font-size", () => {
		const hits = scan(/\bfont-size\s*=\s*["'{][^"'}]*["'}]/g, () => false);
		expect(report(hits)).toBe("");
	});

	it("R10 no Tailwind arbitrary text size utility is used", () => {
		const hits = scan(
			/(?<![\w-])text-\[([^\]]*)\]/g,
			(match) => !/(\d(px|rem|em|pt|%|vw|vh)|length:)/.test(match[1]),
		);
		expect(report(hits)).toBe("");
	});

	it("R10 no named Tailwind size utility falls outside the four tokens", () => {
		const hits = scan(
			/(?<![\w-])text-(?:[2-9]?xl|lg|\dxs)(?![\w-])/g,
			(match) => match[0] === "text-xl",
		);
		expect(report(hits)).toBe("");
	});

	it("R10 no font shorthand sets a size", () => {
		const hits = scan(/(?<![\w-])font\s*:\s*([^;}"'\n]+)/g, (match) =>
			/^(inherit|initial|unset)$/.test(match[1].trim()),
		);
		expect(report(hits)).toBe("");
	});

	it("R10 app.css defines the four type tokens in @theme", () => {
		const css = stripCssComments(readFileSync(cssPath, "utf8"));
		const theme = [...css.matchAll(/@theme[^{]*\{([\s\S]*?)\n\}/g)]
			.map((match) => match[1])
			.join("\n");
		expect(theme).toMatch(/--text-xs:\s*0?\.75rem/);
		expect(theme).toMatch(/--text-sm:\s*0?\.875rem/);
		expect(theme).toMatch(/--text-base:\s*1rem/);
		expect(theme).toMatch(/--text-xl:\s*1\.25rem/);
	});

	it("R11 app.css does not define the --sans token", () => {
		const css = stripCssComments(readFileSync(cssPath, "utf8"));
		expect(css).not.toMatch(/--sans\s*:/);
		expect(css).not.toMatch(/var\(--sans\)/);
	});

	it("R11 app.css keeps --font-sans as the only font stack", () => {
		const css = stripCssComments(readFileSync(cssPath, "utf8"));
		expect(css.match(/--font-sans\s*:/g)).toHaveLength(1);
	});
});
