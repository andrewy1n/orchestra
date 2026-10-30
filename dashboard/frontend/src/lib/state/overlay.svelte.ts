import { tick } from "svelte";
import {
	beginWrite,
	type ConfirmChoice,
	type PendingWrite,
	writeBody,
	writeChoices,
	writePath,
} from "../../actions";
import { getJson, postJson } from "../../api";
import {
	closeDetail,
	type DetailTarget,
	detailTarget,
	openHash,
	phaseHref,
	requirementHref,
	taskHref,
} from "../../detail";
import { detailView, evidenceBoard, taskBoard } from "../../detailView";
import { linkifyText, type RefContext } from "../../links";
import { renderMarkdown } from "../../markdown";
import { buildPhaseChrome } from "../../phaseChrome";
import { buildWaveGraph } from "../../taskGraph";
import type { Snapshot } from "../../types";
import { leaveHref, polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

function escHtml(value: string): string {
	return value
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;");
}

class OverlayState {
	detailPayload: unknown = $state(null);
	detailError = $state("");
	detailLoading = $state(false);

	pendingWrite: PendingWrite | null = $state(null);
	confirmNote = $state("");
	confirmLocalError = $state("");
	writeError = $state("");
	writeBusy = $state(false);

	target: DetailTarget | null = $derived(detailTarget(navigation.route));

	linkCtx: RefContext | null = $derived.by(() => {
		const snapshot = polling.snapshot;
		if (!snapshot) return null;
		const route = navigation.route;
		const target = this.target;
		const effort = polling.effort;
		const phaseSubject = polling.phaseSubject;
		const effortName =
			target?.kind === "phase"
				? (route.parts[1] ?? effort?.effort ?? null)
				: target?.kind === "requirement"
					? (route.parts[1] ?? effort?.effort ?? null)
					: (effort?.effort ?? polling.selectedEffort ?? null);
		const phaseName =
			target?.kind === "phase"
				? (route.parts[2] ?? phaseSubject)
				: target?.kind === "requirement"
					? (route.parts[2] ?? phaseSubject)
					: phaseSubject;
		return {
			snapshot,
			effort: effortName,
			phase: phaseName,
			detail:
				this.detailPayload && typeof this.detailPayload === "object"
					? (this.detailPayload as Record<string, unknown>)
					: null,
		};
	});

	phaseTabs: string[] = $derived.by(() => {
		if (this.target?.kind !== "phase") return [];
		if (!this.detailPayload || typeof this.detailPayload !== "object")
			return [];
		const tabs = (this.detailPayload as { tabs?: unknown }).tabs;
		return Array.isArray(tabs) ? tabs.map(String) : [];
	});

	activePhaseTab = $derived.by(() => {
		const target = this.target;
		if (target?.kind !== "phase") return "";
		if (target.tab && this.phaseTabs.includes(target.tab)) return target.tab;
		return this.phaseTabs[0] ?? "";
	});

	overlayChoices: ConfirmChoice[] = $derived.by(() => {
		const target = this.target;
		if (!target || !this.detailPayload) return [];
		if (target.kind === "needs" || target.kind === "backlog") {
			return writeChoices(target.kind, this.detailPayload);
		}
		return [];
	});

	overlayEffort = $derived.by(() => {
		const target = this.target;
		if (!target) return "";
		if (target.kind === "needs" || target.kind === "backlog") {
			return navigation.route.parts[1] ?? "";
		}
		return "";
	});

	overlayView = $derived.by(() => {
		if (!this.target || !this.detailPayload) return null;
		return detailView(
			this.target.kind,
			this.detailPayload,
			this.activePhaseTab,
		);
	});

	taskView = $derived.by(() => {
		if (
			this.target?.kind !== "phase" ||
			this.activePhaseTab !== "tasks" ||
			!this.detailPayload
		) {
			return null;
		}
		return taskBoard(this.detailPayload);
	});

	evidenceView = $derived.by(() => {
		if (
			this.target?.kind !== "phase" ||
			this.activePhaseTab !== "evidence" ||
			!this.detailPayload
		) {
			return null;
		}
		return evidenceBoard(this.detailPayload);
	});

	phaseChrome = $derived.by(() => {
		if (this.target?.kind !== "phase" || !this.detailPayload) return null;
		return buildPhaseChrome(this.detailPayload, {
			position: polling.effort?.position ?? null,
		});
	});

	phaseTaskGraph = $derived.by(() => {
		if (this.target?.kind !== "phase" || !this.detailPayload) return null;
		if (this.activePhaseTab !== "overview") return null;
		const detail = (this.detailPayload as { detail?: { tasks?: unknown } })
			.detail;
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
		this.detailPayload = null;
		this.detailError = "";
		this.detailLoading = false;
		this.cancelConfirm();
		this.writeError = "";
	}

	linkify(text: string): string {
		if (!this.linkCtx) return escHtml(text);
		return linkifyText(text, this.linkCtx, escHtml);
	}

	md(body: string): string {
		return renderMarkdown(body, this.linkCtx);
	}

	openRequirement(id: string) {
		const route = navigation.route;
		const effortName = route.parts[1] || polling.effort?.effort || "";
		const phaseName = route.parts[2] || "";
		if (!effortName || !phaseName || !id) return;
		openHash(requirementHref(effortName, phaseName, id));
	}

	openGraphTask(id: string) {
		if (!id) return;
		openHash(taskHref(id));
	}

	selectPhaseTab(tab: string) {
		if (!polling.effort || !this.target || this.target.kind !== "phase") return;
		const effortName = navigation.route.parts[1];
		const phaseName = navigation.route.parts[2];
		if (!effortName || !phaseName) return;
		openHash(phaseHref(effortName, phaseName, tab));
	}

	cancelConfirm = () => {
		this.pendingWrite = null;
		this.confirmNote = "";
		this.confirmLocalError = "";
		this.writeBusy = false;
	};

	openConfirm(choice: ConfirmChoice) {
		const target = this.target;
		if (!target || (target.kind !== "needs" && target.kind !== "backlog")) {
			return;
		}
		const effortName = this.overlayEffort;
		if (!effortName || !this.detailPayload) return;
		const pending = beginWrite(
			target.kind,
			effortName,
			this.detailPayload,
			choice,
		);
		if (!pending) return;
		this.pendingWrite = pending;
		this.confirmNote = "";
		this.confirmLocalError = "";
		this.writeError = "";
	}

	async submitConfirm() {
		const pending = this.pendingWrite;
		if (!pending || this.writeBusy) return;
		if (pending.noteRequired && !this.confirmNote.trim()) {
			this.confirmLocalError = "Note required for this action";
			return;
		}
		this.confirmLocalError = "";
		this.writeBusy = true;
		const body = writeBody(pending, this.confirmNote);
		const path = writePath(pending);
		try {
			await postJson<{ ok: boolean }>(path, body);
			this.cancelConfirm();
			this.writeError = "";
			closeDetail(leaveHref());
			try {
				const next = await getJson<Snapshot>("snapshot");
				polling.applySnapshot(next);
			} catch {
				/* poller will catch up */
			}
		} catch (err: unknown) {
			this.writeError = err instanceof Error ? err.message : String(err);
			this.writeBusy = false;
		}
	}
}

export const overlay = new OverlayState();

export function bindOverlay() {
	overlay.reset();

	$effect(() => {
		const next = overlay.target;
		if (!next) {
			overlay.detailPayload = null;
			overlay.detailError = "";
			overlay.detailLoading = false;
			overlay.cancelConfirm();
			overlay.writeError = "";
			return;
		}
		let cancelled = false;
		overlay.detailPayload = null;
		overlay.detailError = "";
		overlay.detailLoading = true;
		overlay.cancelConfirm();
		overlay.writeError = "";
		void getJson<unknown>(next.apiPath)
			.then((data) => {
				if (!cancelled) {
					overlay.detailPayload = data;
					overlay.detailError = "";
					overlay.detailLoading = false;
				}
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					overlay.detailPayload = null;
					overlay.detailError =
						err instanceof Error ? err.message : String(err);
					overlay.detailLoading = false;
				}
			});
		return () => {
			cancelled = true;
		};
	});

	let restoreFocus: HTMLElement | null = null;
	let focusLock = "";

	$effect(() => {
		const target = overlay.target;
		const key = overlay.pendingWrite
			? "confirm"
			: target
				? `detail:${target.kind}`
				: "";
		if (key === focusLock) return;
		const prev = focusLock;
		focusLock = key;
		if (!key) {
			const back = restoreFocus;
			restoreFocus = null;
			if (prev) queueMicrotask(() => back?.focus());
			return;
		}
		if (!prev) {
			const active = document.activeElement;
			if (active instanceof HTMLElement) restoreFocus = active;
		}
		void tick().then(() => {
			const selector = overlay.pendingWrite
				? "[data-confirm-note], [data-confirm-cancel]"
				: '[data-act="close-detail"]';
			document.querySelector<HTMLElement>(selector)?.focus();
		});
	});
}
