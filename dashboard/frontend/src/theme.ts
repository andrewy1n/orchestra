/**
 * Light/dark theme handling.
 *
 * Dark mode is expressed as the `dark` class on `<html>` so Tailwind's
 * class-based variant (declared in `app.css`) can switch the whole page.
 * The same element also carries `data-theme`, which selects the token set
 * borrowed from the design spike (`html[data-theme="dark"]`). The chosen theme
 * is kept in `localStorage`; with none stored, a load starts light and the OS
 * preference is ignored.
 */

export type Theme = "light" | "dark";

export const DEFAULT_THEME: Theme = "light";

const STORAGE_KEY = "theme";

function defaultStorage(): Storage | null {
	try {
		return window.localStorage;
	} catch {
		return null;
	}
}

/** The stored theme, or the default when none is stored, it is unknown, or storage fails. */
export function loadTheme(storage: Storage | null = defaultStorage()): Theme {
	try {
		const stored = storage?.getItem(STORAGE_KEY);
		return stored === "light" || stored === "dark" ? stored : DEFAULT_THEME;
	} catch {
		return DEFAULT_THEME;
	}
}

/** Store `theme`; a failing storage is ignored. */
export function saveTheme(
	theme: Theme,
	storage: Storage | null = defaultStorage(),
): void {
	try {
		storage?.setItem(STORAGE_KEY, theme);
	} catch {}
}

/** The opposite theme. */
export function toggle(theme: Theme): Theme {
	return theme === "dark" ? "light" : "dark";
}

/** Apply `theme` to a root element (`<html>` by default). */
export function applyTheme(
	theme: Theme,
	root: HTMLElement | null = typeof document === "undefined"
		? null
		: document.documentElement,
): void {
	if (!root) return;
	const dark = theme === "dark";
	root.classList.toggle("dark", dark);
	root.dataset.theme = theme;
	root.style.colorScheme = theme;
}
