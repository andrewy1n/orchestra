/**
 * Hash routing.
 *
 * The dashboard is a single page: routes live after the `#` so the FastAPI
 * server only ever has to serve one document. Each screen is a shell for now;
 * later tasks fill them in against the `/api` JSON.
 */

export type RouteName =
	| "home"
	| "task"
	| "phase"
	| "requirement"
	| "needs"
	| "backlog"
	| "record"
	| "picker"
	| "journal"
	| "milestone"
	| "area";

export interface Route {
	/** First path segment, or `home` when the hash is empty. */
	name: RouteName;
	/** Every path segment, decoded. */
	parts: string[];
	/** Raw hash without the leading `#`. */
	raw: string;
}

const NAMES: ReadonlySet<string> = new Set<RouteName>([
	"home",
	"task",
	"phase",
	"requirement",
	"needs",
	"backlog",
	"record",
	"picker",
	"journal",
	"milestone",
	"area",
]);

/** Parse a `location.hash` value into a route. */
export function parseRoute(hash: string): Route {
	const raw = hash.replace(/^#/, "").replace(/^\/+/, "");
	const parts = raw
		.split("/")
		.filter((part) => part.length > 0)
		.map((part) => {
			try {
				return decodeURIComponent(part);
			} catch {
				return part;
			}
		});
	const first = parts[0] ?? "home";
	const name = (NAMES.has(first) ? first : "home") as RouteName;
	return { name, parts, raw };
}

/** The route for the current browser location. */
export function currentRoute(): Route {
	if (typeof window === "undefined")
		return { name: "home", parts: [], raw: "" };
	return parseRoute(window.location.hash);
}

/** A short label for the top bar. */
export function routeLabel(route: Route): string {
	return route.parts.length ? route.parts.join(" / ") : "home";
}

/** Subject of an `#/area/<subject>` route, or an empty string. */
export function areaSubject(route: Route): string {
	return route.name === "area" ? (route.parts[1] ?? "") : "";
}
