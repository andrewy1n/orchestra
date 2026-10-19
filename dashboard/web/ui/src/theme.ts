/**
 * Light/dark theme handling.
 *
 * Dark mode is expressed as the `dark` class on `<html>` so Tailwind's
 * class-based variant (declared in `app.css`) can switch the whole page.
 * The same element also carries `data-theme`, which selects the token set
 * borrowed from the design spike (`html[data-theme="dark"]`). A fresh load
 * starts light: nothing is persisted, and the OS preference is ignored.
 */

export type Theme = "light" | "dark";

export const DEFAULT_THEME: Theme = "light";

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
