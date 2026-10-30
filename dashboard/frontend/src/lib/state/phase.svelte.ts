import { untrack } from "svelte";
import { getJson } from "../../api";
import {
	type DetailTarget,
	detailTarget,
	openHash,
	phaseHref,
} from "../../detail";
import { detailView, evidenceBoard, taskBoard } from "../../detailView";
import { filteredTasks, tabCounts } from "../../efforts";
import type { RefContext } from "../../links";
import { buildPhaseChrome } from "../../phaseChrome";
import { buildWaveGraph } from "../../taskGraph";
import type { EffortView, StatusTab } from "../../types";
import { polling } from "./polling.svelte";
import { linkContext } from "./refs";
import { navigation } from "./route.svelte";

class PhaseState {
	payload: unknown = $state(null);
	error = $state("");
	loading = $state(false);
	statusTab: StatusTab = $state("active");
	tabPinnedFor = $state("");

	target: DetailTarget | null = $derived.by(() => {
		const target = detailTarget(navigation.route);
		return target?.kind === "phase" ? target : null;
	});

	apiPath = $derived(this.target?.apiPath ?? "");

	linkCtx: RefContext | null = $derived.by(() => {
		if (!this.target) return null;
		const route = navigation.route;
		return linkContext(
			route.parts[1] ?? polling.effort?.effort ?? null,
			route.parts[2] ?? polling.phaseSubject,
			this.payload,
		);
	});

	routeEffort: EffortView | null = $derived.by(() => {
		if (!this.target) return null;
		const name = navigation.route.parts[1];
		return (
			polling.snapshot?.efforts.find((view) => view.effort === name) ?? null
		);
	});

	routePhase: string | null = $derived(
		this.target ? (navigation.route.parts[2] ?? null) : null,
	);

	routeKey = $derived(
		this.routeEffort && this.routePhase
			? `${this.routeEffort.effort}/${this.routePhase}`
			: "",
	);

	counts = $derived(
		this.routeEffort ? tabCounts(this.routeEffort, this.routePhase) : null,
	);

	tasks = $derived(
		this.routeEffort
			? filteredTasks(this.routeEffort, this.routePhase, this.statusTab)
			: [],
	);

	phaseTabs: string[] = $derived.by(() => {
		if (!this.target) return [];
		if (!this.payload || typeof this.payload !== "object") return [];
		const tabs = (this.payload as { tabs?: unknown }).tabs;
		return Array.isArray(tabs) ? tabs.map(String) : [];
	});

	activePhaseTab = $derived.by(() => {
		const target = this.target;
		if (!target) return "";
		if (target.tab && this.phaseTabs.includes(target.tab)) return target.tab;
		return this.phaseTabs[0] ?? "";
	});

	view = $derived.by(() => {
		if (!this.target || !this.payload) return null;
		return detailView("phase", this.payload, this.activePhaseTab);
	});

	state = $derived.by(() => {
		const detail = (this.payload as { detail?: { state?: unknown } } | null)
			?.detail;
		return String(detail?.state ?? "").replace(/_/g, " ");
	});

	taskView = $derived.by(() => {
		if (!this.target || this.activePhaseTab !== "tasks" || !this.payload) {
			return null;
		}
		return taskBoard(this.payload);
	});

	evidenceView = $derived.by(() => {
		if (!this.target || this.activePhaseTab !== "evidence" || !this.payload) {
			return null;
		}
		return evidenceBoard(this.payload);
	});

	phaseChrome = $derived.by(() => {
		if (!this.target || !this.payload) return null;
		return buildPhaseChrome(this.payload, {
			position: polling.effort?.position ?? null,
		});
	});

	phaseTaskGraph = $derived.by(() => {
		if (!this.target || !this.payload) return null;
		if (this.activePhaseTab !== "overview") return null;
		const detail = (this.payload as { detail?: { tasks?: unknown } }).detail;
		const tasks = Array.isArray(detail?.tasks) ? detail.tasks : [];
		return buildWaveGraph(
			tasks
				.map((row) => {
					const task = row as {
						id?: string;
						subject?: string;
						title?: string;
						status?: string;
						wave?: number | null;
						depends_on?: string[];
						waits_on?: string[];
					};
					return {
						id: String(task.id || ""),
						subject: task.subject,
						title: task.title,
						status: String(task.status || ""),
						wave: task.wave,
						depends_on: task.depends_on,
						waits_on: task.waits_on,
					};
				})
				.filter((task) => task.id),
		);
	});

	reset() {
		this.payload = null;
		this.error = "";
		this.loading = false;
		this.statusTab = "active";
		this.tabPinnedFor = "";
	}

	chooseTab(name: StatusTab) {
		this.statusTab = name;
		this.tabPinnedFor = this.routeKey;
	}

	selectPhaseTab(tab: string) {
		if (!polling.effort || !this.target) return;
		const effortName = navigation.route.parts[1];
		const phaseName = navigation.route.parts[2];
		if (!effortName || !phaseName) return;
		openHash(phaseHref(effortName, phaseName, tab));
	}
}

export const phase = new PhaseState();

export function bindPhase() {
	phase.reset();

	$effect(() => {
		phase.routeKey;
		untrack(() => {
			phase.statusTab = "active";
			phase.tabPinnedFor = "";
		});
	});

	$effect(() => {
		const current = phase.routeEffort;
		if (!current || phase.tabPinnedFor === phase.routeKey) return;
		const nextCounts = tabCounts(current, phase.routePhase);
		if (
			current.needs_you.length > 0 &&
			nextCounts.active === 0 &&
			phase.statusTab === "active"
		) {
			const fallback =
				(["done", "waiting", "ready", "running", "all"] as StatusTab[]).find(
					(name) => nextCounts[name] > 0,
				) ?? "all";
			phase.statusTab = fallback;
		}
	});

	$effect(() => {
		const path = phase.apiPath;
		if (!path) {
			phase.reset();
			return;
		}
		let cancelled = false;
		phase.payload = null;
		phase.error = "";
		phase.loading = true;
		void getJson<unknown>(path)
			.then((data) => {
				if (!cancelled) {
					phase.payload = data;
					phase.error = "";
					phase.loading = false;
				}
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					phase.payload = null;
					phase.error = err instanceof Error ? err.message : String(err);
					phase.loading = false;
				}
			});
		return () => {
			cancelled = true;
		};
	});
}
