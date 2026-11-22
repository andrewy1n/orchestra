// @vitest-environment jsdom

import { readdirSync, readFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

function testFiles(dir: string): string[] {
	return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
		const full = join(dir, entry.name);
		if (entry.isDirectory()) return testFiles(full);
		return entry.name.endsWith(".test.ts") ? [full] : [];
	});
}

const SELF = new Set(["mountGuard.test.ts"]);
const SWALLOWING_HELPER = new RegExp(
	[
		"(?:async\\s+)?function\\s+tryMount\\w*",
		"(?:const|let)\\s+tryMount\\w*\\s*=",
	].join("|"),
);
const SWALLOWED_CATCH =
	/catch\s*(?:\([^)]*\))?\s*\{[^}]*return\s+false\s*;?\s*\}/;

describe("test files do not define swallowing mount helpers", () => {
	const root = resolve(process.cwd(), "src");
	const files = testFiles(root).filter(
		(file) => !SELF.has(file.split("/").pop() ?? ""),
	);

	it("finds the dashboard test files", () => {
		expect(files.length).toBeGreaterThan(10);
	});

	it("no test file defines its own tryMount helper", () => {
		const offenders = files
			.filter((file) => SWALLOWING_HELPER.test(readFileSync(file, "utf8")))
			.map((file) => relative(root, file));
		expect(offenders).toEqual([]);
	});

	it("no test file swallows a mount error by returning false from a catch", () => {
		const offenders = files
			.filter((file) => SWALLOWED_CATCH.test(readFileSync(file, "utf8")))
			.map((file) => relative(root, file));
		expect(offenders).toEqual([]);
	});
});
