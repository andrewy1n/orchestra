import { openHash, phaseHref } from "../../detail";
import {
	defaultPhase,
	filteredTasks,
	resolvedPhase,
	tabCounts,
	visibleEfforts,
} from "../../efforts";
import {
	groupPhasesByMilestone,
	initialExpandedMilestones,
} from "../../milestones";
import { startTokenPoller } from "../../poll";
import { openBacklog } from "../../side";
import type { EffortView, Snapshot, StatusTab } from "../../types";
import { navigation } from "./route.svelte";

const JOURNAL_TEASER_KINDS = new Set(["repair", "evaluate"]);

class Polling {
	snapshot = $state<Snapshot | null>(null);
	loading = $state(true);
	error = $state("");
	pollError = $state("");

	selectedEffort = $state("");
	/** null = follow default; "all" = every phase; else a phase subject. */
	pinnedPhase: string | null = $state(null);
	statusTab: StatusTab = $state("active");
	/** Effort whose status tab the user picked. Empty follows the default. */
	tabPinnedFor = $state("");
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

	phaseSubject: string | null = $derived(
		this.effort ? resolvedPhase(this.effort, this.pinnedPhase) : null,
	);

	tasks = $derived(
		this.effort
			? filteredTasks(this.effort, this.phaseSubject, this.statusTab)
			: [],
	);

	showNeedsInMain = $derived(
		!!this.effort &&
			navigation.route.name !== "journal" &&
			this.effort.needs_you.length > 0,
	);

	counts = $derived(
		this.effort ? tabCounts(this.effort, this.phaseSubject) : null,
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
		this.pinnedPhase = null;
		this.statusTab = "active";
		this.tabPinnedFor = "";
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
		this.pinnedPhase = null;
		this.statusTab = "active";
		this.tabPinnedFor = "";
	}

	chooseTab(name: StatusTab) {
		this.statusTab = name;
		this.tabPinnedFor = this.effort?.effort ?? "";
	}

	selectPhase(targetPhase: string) {
		const effort = this.effort;
		if (!effort) return;
		if (targetPhase === "all") {
			this.pinnedPhase = "all";
			return;
		}
		this.pinnedPhase =
			targetPhase === defaultPhase(effort) ? null : targetPhase;
	}

	activatePhase(subject: string) {
		const phaseSubject = this.phaseSubject;
		if (phaseSubject === subject) openPhase(subject);
		else this.selectPhase(subject);
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

function openPhase(subject: string) {
	if (!polling.effort) return;
	openHash(phaseHref(polling.effort.effort, subject));
}

export function bindPolling() {
	polling.reset();
	navigation.reset();

	$effect(() => {
		const current = polling.effort;
		if (!current || polling.tabPinnedFor === current.effort) return;
		const nextCounts = tabCounts(current, polling.phaseSubject);
		if (
			current.needs_you.length > 0 &&
			nextCounts.active === 0 &&
			polling.statusTab === "active"
		) {
			const fallback =
				(["done", "waiting", "ready", "running", "all"] as StatusTab[]).find(
					(name) => nextCounts[name] > 0,
				) ?? "all";
			polling.statusTab = fallback;
		}
	});

	$effect(() => {
		const current = polling.effort;
		if (!current?.milestones?.length) {
			polling.expandedForEffort = "";
			polling.expandedMilestones = new Set();
			return;
		}
		if (polling.expandedForEffort === current.effort) return;
		polling.expandedForEffort = current.effort;
		polling.expandedMilestones = initialExpandedMilestones(
			current,
			polling.pinnedPhase,
		);
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
		const phases = view.phases.filter((row) => row.milestone === milestoneKey);
		if (
			phases.length === 1 &&
			phases[0] &&
			polling.pinnedPhase !== phases[0].subject
		) {
			polling.pinnedPhase = phases[0].subject;
		}
	});
}
