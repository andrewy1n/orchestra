import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const cssPath = path.join(srcDir, "app.css");

interface Rule {
	selector: string;
	line: number;
	atRules: string[];
}

function blank(text: string, pattern: RegExp): string {
	return text.replace(pattern, (match) => match.replace(/[^\n]/g, " "));
}

function parseRules(css: string): Rule[] {
	const clean = blank(
		blank(css, /\/\*[\s\S]*?\*\//g),
		/"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'/g,
	);
	const rules: Rule[] = [];
	const stack: { prelude: string; isAtRule: boolean }[] = [];
	let prelude = "";
	let preludeStart = 0;
	let line = 1;
	for (const char of clean) {
		if (char === "{") {
			const text = prelude.trim();
			const isAtRule = text.startsWith("@");
			if (!isAtRule) {
				rules.push({
					selector: text,
					line: preludeStart,
					atRules: stack.filter((s) => s.isAtRule).map((s) => s.prelude),
				});
			}
			stack.push({ prelude: text, isAtRule });
			prelude = "";
		} else if (char === "}" || char === ";") {
			if (char === "}") stack.pop();
			prelude = "";
		} else {
			if (prelude.trim() === "" && char.trim() !== "") preludeStart = line;
			prelude += char;
		}
		if (char === "\n") line += 1;
	}
	return rules;
}

function isGlobalFocusVisible(selector: string): boolean {
	return selector
		.split(",")
		.map((part) => part.trim())
		.some((part) => part === ":focus-visible" || part === "*:focus-visible");
}

function unlayeredFocusRules(css: string): Rule[] {
	return parseRules(css).filter(
		(rule) =>
			isGlobalFocusVisible(rule.selector) &&
			!rule.atRules.some((at) => /^@layer\b/.test(at)),
	);
}

describe("focus layer", () => {
	it("R26 app.css declares no global :focus-visible rule outside a cascade layer", () => {
		const hits = unlayeredFocusRules(readFileSync(cssPath, "utf8"));
		expect(hits.map((rule) => `app.css:${rule.line} ${rule.selector}`)).toEqual(
			[],
		);
	});

	it("R26 app.css still declares the global :focus-visible rule inside a layer", () => {
		const layered = parseRules(readFileSync(cssPath, "utf8")).filter(
			(rule) =>
				isGlobalFocusVisible(rule.selector) &&
				rule.atRules.some((at) => /^@layer\b/.test(at)),
		);
		expect(layered).toHaveLength(1);
	});

	it("R26 scan flags a bare rule, including one nested in @media", () => {
		const css =
			"@layer base { a { color: red } }\n@media (min-width: 1px) {\n  :focus-visible { outline: 0 }\n}";
		expect(unlayeredFocusRules(css)).toHaveLength(1);
	});

	it("R26 scan accepts a rule nested in @media inside @layer", () => {
		const css =
			"@layer base {\n@media (min-width: 1px) {\n  :focus-visible { outline: 0 }\n}\n}";
		expect(unlayeredFocusRules(css)).toHaveLength(0);
	});

	it("R26 scan ignores comments and selectors that only contain :focus-visible", () => {
		const css =
			"/* :focus-visible { } */\n.a:focus-visible { outline: 0 }\n@layer x;\n";
		expect(unlayeredFocusRules(css)).toHaveLength(0);
	});
});
