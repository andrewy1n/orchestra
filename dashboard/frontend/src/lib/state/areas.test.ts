import { describe, expect, it } from "vitest";
import type { AreaView } from "../../api-types";
import { areaHref, effortHref } from "../../detail";
import { parseRoute } from "../../router";
import type { DeepPartial, EffortView, Snapshot } from "../../types";
import { areaRollup, breadcrumbParts, groupByArea, railItems } from "./areas";

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		area: "",
		finished: false,
		phases: [],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

function area(subject: string, title = subject, openCount = 0): AreaView {
	return { subject, title, scope: "", open_count: openCount, ideas: [] };
}

function snapshotOf(efforts: EffortView[]): Snapshot {
	return {
		token: "t",
		generated_at: "2026-01-01T00:00:00Z",
		efforts,
	} as Snapshot;
}

const need = { kind: "question", id: "n", subject: "s", text: "t" };

const billing = area("billing", "Billing", 3);
const growth = area("growth", "Growth", 1);
const areas = [billing, growth];

const efforts = [
	effort({ effort: "invoices", area: "billing", needs_you: [need, need] }),
	effort({ effort: "signup", area: "growth", finished: true }),
	effort({ effort: "refunds", area: "billing" }),
	effort({ effort: "loose" }),
	effort({ effort: "ghost", area: "missing" }),
];
const snapshot = snapshotOf(efforts);

describe("groupByArea", () => {
	it("groups efforts in the order of the areas", () => {
		const { groups } = groupByArea(efforts, [growth, billing]);
		expect(groups.map((g) => g.area.subject)).toEqual(["growth", "billing"]);
		expect(groups[1]?.efforts.map((e) => e.effort)).toEqual([
			"invoices",
			"refunds",
		]);
	});

	it("puts efforts with an empty or unknown area in unplaced", () => {
		const { unplaced } = groupByArea(efforts, areas);
		expect(unplaced.map((e) => e.effort)).toEqual(["loose", "ghost"]);
	});

	it("keeps an area with no efforts as an empty group", () => {
		const { groups } = groupByArea([], areas);
		expect(groups.map((g) => g.efforts.length)).toEqual([0, 0]);
	});
});

describe("areaRollup", () => {
	it("counts efforts, open ideas and needs for the area", () => {
		expect(areaRollup(efforts, billing)).toEqual({
			efforts: 2,
			openIdeas: 3,
			needs: 2,
		});
		expect(areaRollup(efforts, growth)).toEqual({
			efforts: 1,
			openIdeas: 1,
			needs: 0,
		});
	});
});

describe("railItems", () => {
	it("has no items at the product level", () => {
		expect(railItems(parseRoute(""), snapshot, areas)).toEqual({
			level: "product",
			items: [],
		});
	});

	it("lists the areas on an area route and marks the current one", () => {
		const rail = railItems(parseRoute(areaHref("growth")), snapshot, areas);
		expect(rail.level).toBe("area");
		expect(rail.items.map((i) => [i.key, i.label, i.href, i.current])).toEqual([
			["billing", "Billing", "#/area/billing", false],
			["growth", "Growth", "#/area/growth", true],
		]);
	});

	it("lists the efforts of the area of the current effort", () => {
		const rail = railItems(parseRoute(effortHref("refunds")), snapshot, areas);
		expect(rail.level).toBe("effort");
		expect(rail.items.map((i) => [i.key, i.href, i.current, i.needs])).toEqual([
			["invoices", "#/effort/invoices", false, 2],
			["refunds", "#/effort/refunds", true, 0],
		]);
	});

	it("lists the efforts with no area when the current effort has none", () => {
		const rail = railItems(parseRoute(effortHref("loose")), snapshot, areas);
		expect(rail.items.map((i) => i.key)).toEqual(["loose", "ghost"]);
	});

	it("marks finished efforts", () => {
		const rail = railItems(parseRoute(effortHref("signup")), snapshot, areas);
		expect(rail.items.map((i) => i.finished)).toEqual([true]);
	});

	it("uses the effort level on routes that show an effort", () => {
		const phase = railItems(parseRoute("#/phase/invoices/p1"), snapshot, areas);
		expect(phase.level).toBe("effort");
		expect(phase.items.find((i) => i.current)?.key).toBe("invoices");
	});
});

describe("breadcrumbParts", () => {
	it("shows only Product on the home route", () => {
		expect(breadcrumbParts(parseRoute(""), snapshot, areas)).toEqual([
			{ label: "Product" },
		]);
	});

	it("shows Product and the area title on an area route", () => {
		expect(
			breadcrumbParts(parseRoute(areaHref("billing")), snapshot, areas),
		).toEqual([{ label: "Product", href: "#/" }, { label: "Billing" }]);
	});

	it("shows Product, area and effort on an effort route", () => {
		expect(
			breadcrumbParts(parseRoute(effortHref("refunds")), snapshot, areas),
		).toEqual([
			{ label: "Product", href: "#/" },
			{ label: "Billing", href: "#/area/billing" },
			{ label: "refunds" },
		]);
	});

	it("omits the area part when the effort has no area", () => {
		expect(
			breadcrumbParts(parseRoute(effortHref("loose")), snapshot, areas),
		).toEqual([{ label: "Product", href: "#/" }, { label: "loose" }]);
	});

	it("reuses the effort level on other routes", () => {
		expect(
			breadcrumbParts(parseRoute("#/phase/invoices/p1"), snapshot, areas),
		).toEqual([
			{ label: "Product", href: "#/" },
			{ label: "Billing", href: "#/area/billing" },
			{ label: "invoices" },
		]);
	});
});
