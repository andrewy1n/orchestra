import { describe, expect, it } from "vitest";
import { loadTheme, saveTheme } from "./theme";

function memoryStorage(initial: Record<string, string> = {}): Storage {
	const data = new Map(Object.entries(initial));
	return {
		get length() {
			return data.size;
		},
		clear: () => data.clear(),
		getItem: (key) => data.get(key) ?? null,
		key: (index) => [...data.keys()][index] ?? null,
		removeItem: (key) => void data.delete(key),
		setItem: (key, value) => void data.set(key, value),
	};
}

const throwingStorage: Storage = {
	length: 0,
	clear() {
		throw new Error("blocked");
	},
	getItem() {
		throw new Error("blocked");
	},
	key() {
		throw new Error("blocked");
	},
	removeItem() {
		throw new Error("blocked");
	},
	setItem() {
		throw new Error("blocked");
	},
};

describe("loadTheme", () => {
	it("returns dark when dark is stored", () => {
		expect(loadTheme(memoryStorage({ theme: "dark" }))).toBe("dark");
	});

	it("returns light when light is stored", () => {
		expect(loadTheme(memoryStorage({ theme: "light" }))).toBe("light");
	});

	it("returns light when nothing is stored", () => {
		expect(loadTheme(memoryStorage())).toBe("light");
	});

	it("returns light for an unknown stored value", () => {
		expect(loadTheme(memoryStorage({ theme: "Dark" }))).toBe("light");
	});

	it("returns light when storage throws", () => {
		expect(loadTheme(throwingStorage)).toBe("light");
	});
});

describe("saveTheme", () => {
	it("stores the theme under the key theme", () => {
		const storage = memoryStorage();
		saveTheme("dark", storage);
		expect(storage.getItem("theme")).toBe("dark");
	});

	it("does not throw when storage throws", () => {
		expect(() => saveTheme("dark", throwingStorage)).not.toThrow();
	});
});
