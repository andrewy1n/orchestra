import type { AreaView } from "../../api-types";
import { areaHref, effortHref } from "../../detail";
import { areaSubject, type Route } from "../../router";
import type { EffortView, Snapshot } from "../../types";

export interface AreaGroup {
	area: AreaView;
	efforts: EffortView[];
}

export interface AreaRollup {
	efforts: number;
	openIdeas: number;
	needs: number;
}

export interface RailItem {
	key: string;
	label: string;
	href: string;
	current: boolean;
	finished: boolean;
	needs: number;
}

export interface Rail {
	level: "product" | "area" | "effort";
	items: RailItem[];
}

export interface CrumbPart {
	label: string;
	href?: string;
}

const EFFORT_ROUTES: ReadonlySet<string> = new Set([
	"effort",
	"task",
	"phase",
	"requirement",
	"needs",
	"backlog",
	"record",
	"milestone",
	"journal",
]);

export function groupByArea(
	efforts: EffortView[],
	areas: AreaView[],
): { groups: AreaGroup[]; unplaced: EffortView[] } {
	const known = new Set(areas.map((area) => area.subject));
	return {
		groups: areas.map((area) => ({
			area,
			efforts: efforts.filter((view) => view.area === area.subject),
		})),
		unplaced: efforts.filter((view) => !known.has(view.area)),
	};
}

export function firstSentence(markdown: string): string {
	const plain = markdown
		.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
		.replace(/^\s*(#{1,6}|>|[-*+])\s+/gm, "")
		.replace(/[*_`]/g, "")
		.replace(/\s+/g, " ")
		.trim();
	const end = plain.search(/\.(\s|$)/);
	return end === -1 ? plain : plain.slice(0, end + 1);
}

export function areaRollup(efforts: EffortView[], area: AreaView): AreaRollup {
	const inArea = efforts.filter((view) => view.area === area.subject);
	return {
		efforts: inArea.length,
		openIdeas: area.open_count,
		needs: inArea.reduce((sum, view) => sum + view.needs_you.length, 0),
	};
}

function routeEffort(
	route: Route,
	efforts: EffortView[],
	selected: string,
): EffortView | null {
	if (!EFFORT_ROUTES.has(route.name)) return null;
	let name = selected;
	if (route.name === "task") {
		const id = route.parts[1] ?? "";
		name =
			efforts.find((view) => view.tasks.some((task) => task.id === id))
				?.effort ?? selected;
	} else if (route.name !== "journal" && route.name !== "record") {
		name = route.parts[1] ?? selected;
	}
	return (
		efforts.find((view) => view.effort === name) ??
		(name ? null : (efforts[0] ?? null))
	);
}

export function railItems(
	route: Route,
	snapshot: Snapshot | null,
	areas: AreaView[],
	selected = "",
): Rail {
	const efforts = snapshot?.efforts ?? [];
	if (route.name === "area") {
		const subject = areaSubject(route);
		return {
			level: "area",
			items: areas.map((area) => ({
				key: area.subject,
				label: area.title,
				href: areaHref(area.subject),
				current: area.subject === subject,
				finished: false,
				needs: areaRollup(efforts, area).needs,
			})),
		};
	}
	const current = routeEffort(route, efforts, selected);
	if (!current) {
		return {
			level: EFFORT_ROUTES.has(route.name) ? "effort" : "product",
			items: [],
		};
	}
	const known = new Set(areas.map((area) => area.subject));
	const siblings = efforts.filter((view) =>
		known.has(current.area)
			? view.area === current.area
			: !known.has(view.area),
	);
	return {
		level: "effort",
		items: siblings.map((view) => ({
			key: view.effort,
			label: view.effort,
			href: effortHref(view.effort),
			current: view.effort === current.effort,
			finished: view.finished,
			needs: view.needs_you.length,
		})),
	};
}

export function breadcrumbParts(
	route: Route,
	snapshot: Snapshot | null,
	areas: AreaView[],
	selected = "",
): CrumbPart[] {
	const product: CrumbPart = { label: "Product", href: "#/" };
	const finish = (parts: CrumbPart[]): CrumbPart[] =>
		parts.map((part, index) =>
			index === parts.length - 1 ? { label: part.label } : part,
		);
	if (route.name === "home") return finish([product]);
	if (route.name === "area") {
		const subject = areaSubject(route);
		const title = areas.find((area) => area.subject === subject)?.title;
		return finish([product, { label: title ?? subject }]);
	}
	const current = routeEffort(route, snapshot?.efforts ?? [], selected);
	if (!current) return finish([product]);
	const parts = [product];
	const owner = areas.find((area) => area.subject === current.area);
	if (owner) parts.push({ label: owner.title, href: areaHref(owner.subject) });
	parts.push({ label: current.effort, href: effortHref(current.effort) });
	return finish(parts);
}
