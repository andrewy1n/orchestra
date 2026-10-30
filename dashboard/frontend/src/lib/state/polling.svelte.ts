import { untrack } from "svelte";
import { effortHref, phaseHref } from "../../detail";
import { visibleEfforts } from "../../efforts";
import {
	groupPhasesByMilestone,
	initialExpandedMilestones,
} from "../../milestones";
import { startTokenPoller } from "../../poll";
import { effortName } from "../../router";
import { openBacklog } from "../../side";
import type { EffortView, Snapshot } from "../../types";
import { routeEffort, routePhase } from "./areas";
import { navigation } from "./route.svelte";

const JOURNAL_TEASER_KINDS = new Set(["repair", "evaluate"]);

class Polling {
	snapshot = $state<Snapshot | null>(null);
	loading = $state(true);
	error = $state("");
	pollError = $state("");

	selectedEffort = $state("");
	showFinished = $state(false);
	/** Milestone subjects currently expanded in the Phases block. */
	expandedMilestones: Set<string> = $state(new Set());
	/** Effort name that `expandedMilestones` was initialized for. */
	expandedForEffort = $state("");

	rail = $derived(
		this.snapshot
			? visibleEfforts(this.snapshot.efforts, this.showFinished)
			: { shown: [] as EffortView[], hidden: 0 },
	);

	effort: EffortView | null = $derived.by(() => {
		const snapshot = this.snapshot;
		if (!snapshot) return null;
		const name = this.selectedEffort || this.rail.shown[0]?.effort || "";
		return snapshot.efforts.find((view) => view.effort === name) ?? null;
	});

	showNeedsInMain = $derived(
		!!this.effort &&
			navigation.route.name !== "journal" &&
			this.effort.needs_you.length > 0,
	);

	hasMilestones = $derived((this.effort?.milestones?.length ?? 0) > 0);

	milestoneGroups = $derived(
		this.effort && this.hasMilestones
			? groupPhasesByMilestone(this.effort)
			: [],
	);

	backlogItems = $derived(openBacklog(this.effort));

	showJournalTeaser = $derived(
		!!this.effort && JOURNAL_TEASER_KINDS.has(this.effort.kind),
	);

	reset() {
		this.snapshot = null;
		this.loading = true;
		this.error = "";
		this.pollError = "";
		this.selectedEffort = "";
		this.showFinished = false;
		this.expandedMilestones = new Set();
		this.expandedForEffort = "";
	}

	applySnapshot = (data: Snapshot) => {
		this.snapshot = data;
		this.loading = false;
		this.error = "";
		this.pollError = "";
		if (!this.selectedEffort) {
			const { shown } = visibleEfforts(data.efforts, this.showFinished);
			if (shown[0]) this.selectedEffort = shown[0].effort;
		}
	};

	selectEffort(name: string) {
		this.selectedEffort = name;
	}

	toggleMilestone(key: string) {
		const next = new Set(this.expandedMilestones);
		if (next.has(key)) next.delete(key);
		else next.add(key);
		this.expandedMilestones = next;
	}

	start(): () => void {
		const poller = startTokenPoller({
			onSnapshot: this.applySnapshot,
			onError: (message) => {
				if (this.loading) {
					this.loading = false;
					this.error = message;
				} else {
					this.pollError = message;
				}
			},
		});
		return () => poller.stop();
	}
}

export const polling = new Polling();

export function leaveHref(): string {
	const route = navigation.route;
	if (route.name === "task" || route.name === "requirement") {
		const onPhase = routePhase(route, polling.snapshot?.efforts ?? []);
		if (onPhase) return phaseHref(onPhase.effort.effort, onPhase.phase.subject);
	}
	const name =
		routeEffort(
			navigation.route,
			polling.snapshot?.efforts ?? [],
			polling.selectedEffort,
		)?.effort ?? polling.selectedEffort;
	return name ? effortHref(name) : "";
}

export function bindPolling() {
	polling.reset();
	navigation.reset();

	$effect(() => {
		const current = polling.effort;
		if (!current?.milestones?.length) {
			polling.expandedForEffort = "";
			polling.expandedMilestones = new Set();
			return;
		}
		if (polling.expandedForEffort === current.effort) return;
		polling.expandedForEffort = current.effort;
		polling.expandedMilestones = initialExpandedMilestones(current);
	});

	$effect(() => {
		const name = effortName(navigation.route);
		if (name && untrack(() => polling.selectedEffort) !== name)
			polling.selectEffort(name);
	});

	$effect(() => {
		const route = navigation.route;
		if (route.name !== "milestone") return;
		const effortName = route.parts[1] ?? "";
		const milestoneKey = route.parts[2] ?? "";
		const snapshot = polling.snapshot;
		if (!effortName || !milestoneKey || !snapshot) return;
		if (polling.selectedEffort !== effortName)
			polling.selectedEffort = effortName;
		const view = snapshot.efforts.find((row) => row.effort === effortName);
		if (!view) return;
		if (
			polling.expandedForEffort !== effortName ||
			!polling.expandedMilestones.has(milestoneKey)
		) {
			polling.expandedForEffort = effortName;
			const next = new Set(polling.expandedMilestones);
			next.add(milestoneKey);
			polling.expandedMilestones = next;
		}
	});
}
