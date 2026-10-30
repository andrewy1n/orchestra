import { untrack } from "svelte";
import { getJson } from "../../api";
import { detailTarget, openHash, phaseHref } from "../../detail";
import { detailView, evidenceBoard, taskBoard } from "../../detailView";
import { filteredTasks, tabCounts } from "../../efforts";
import type { RefContext } from "../../links";
import { buildPhaseChrome } from "../../phaseChrome";
import { buildWaveGraph } from "../../taskGraph";
import type { EffortView, StatusTab } from "../../types";
import { routePhase } from "./areas";
import { polling } from "./polling.svelte";
import { linkContext } from "./refs";
import { navigation } from "./route.svelte";

class PhaseState {
	payload: unknown = $state(null);
	error = $state("");
	loading = $state(false);
	statusTab: StatusTab = $state("active");
	tabPinnedFor = $state("");

	keptTab: string | undefined = $state(undefined);
	keptFor = $state("");

	page: { effort: string; phase: string; tab?: string } | null = $derived.by(
		() => {
			const route = navigation.route;
			if (route.name === "task") {
				const onPhase = routePhase(route, polling.snapshot?.efforts ?? []);
				return onPhase
					? {
							effort: onPhase.effort.effort,
							phase: onPhase.phase.subject,
							tab: this.keptTab,
						}
					: null;
			}
			if (route.name !== "phase" && route.name !== "requirement") return null;
			const target = detailTarget(route);
			const effort = route.parts[1];
			const phase = route.parts[2];
			if (!target || !effort || !phase) return null;
			return {
				effort,
				phase,
				tab: route.name === "phase" ? target.tab : this.keptTab,
			};
		},
	);

	apiPath = $derived(
		this.page
			? `phase?effort=${encodeURIComponent(this.page.effort)}&phase=${encodeURIComponent(this.page.phase)}`
			: "",
	);

	linkCtx: RefContext | null = $derived.by(() => {
		if (!this.page) return null;
		return linkContext(this.page.effort, this.page.phase, this.payload);
	});

	routeEffort: EffortView | null = $derived.by(() => {
		if (!this.page) return null;
		const name = this.page.effort;
		return (
			polling.snapshot?.efforts.find((view) => view.effort === name) ?? null
		);
	});

	routePhase: string | null = $derived(this.page?.phase ?? null);

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
		if (!this.page) return [];
		if (!this.payload || typeof this.payload !== "object") return [];
		const tabs = (this.payload as { tabs?: unknown }).tabs;
		return Array.isArray(tabs) ? tabs.map(String) : [];
	});

	activePhaseTab = $derived.by(() => {
		const tab = this.page?.tab;
		if (!this.page) return "";
		if (tab && this.phaseTabs.includes(tab)) return tab;
		return this.phaseTabs[0] ?? "";
	});

	view = $derived.by(() => {
		if (!this.page || !this.payload) return null;
		return detailView("phase", this.payload, this.activePhaseTab);
	});

	state = $derived.by(() => {
		const detail = (this.payload as { detail?: { state?: unknown } } | null)
			?.detail;
		return String(detail?.state ?? "").replace(/_/g, " ");
	});

	taskView = $derived.by(() => {
		if (!this.page || this.activePhaseTab !== "tasks" || !this.payload) {
			return null;
		}
		return taskBoard(this.payload);
	});

	evidenceView = $derived.by(() => {
		if (!this.page || this.activePhaseTab !== "evidence" || !this.payload) {
			return null;
		}
		return evidenceBoard(this.payload);
	});

	phaseChrome = $derived.by(() => {
		if (!this.page || !this.payload) return null;
		return buildPhaseChrome(this.payload, {
			position: polling.effort?.position ?? null,
		});
	});

	phaseTaskGraph = $derived.by(() => {
		if (!this.page || !this.payload) return null;
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
		this.keptTab = undefined;
		this.keptFor = "";
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
		if (!this.page) return;
		openHash(phaseHref(this.page.effort, this.page.phase, tab));
	}
}

export const phase = new PhaseState();

export function bindPhase() {
	phase.reset();

	$effect(() => {
		const route = navigation.route;
		const key = phase.routeKey;
		untrack(() => {
			if (route.name === "phase") {
				phase.keptTab = detailTarget(route)?.tab;
				phase.keptFor = key;
			} else if (key !== phase.keptFor) {
				phase.keptTab = undefined;
				phase.keptFor = key;
			}
		});
	});

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
