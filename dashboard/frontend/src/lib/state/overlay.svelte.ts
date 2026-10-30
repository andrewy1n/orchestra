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
import { closeDetail, type DetailTarget, leafTarget } from "../../detail";
import { detailView } from "../../detailView";
import { defaultPhase } from "../../efforts";
import type { RefContext } from "../../links";
import type { Snapshot } from "../../types";
import { routePhase } from "./areas";
import { leaveHref, polling } from "./polling.svelte";
import { linkContext } from "./refs";
import { navigation } from "./route.svelte";

class OverlayState {
	detailPayload: unknown = $state(null);
	detailError = $state("");
	detailLoading = $state(false);

	pendingWrite: PendingWrite | null = $state(null);
	confirmNote = $state("");
	confirmLocalError = $state("");
	writeError = $state("");
	writeBusy = $state(false);

	target: DetailTarget | null = $derived(leafTarget(navigation.route));

	linkCtx: RefContext | null = $derived.by(() => {
		const route = navigation.route;
		const target = this.target;
		const effort = polling.effort;
		const efforts = polling.snapshot?.efforts ?? [];
		const effortName =
			target?.kind === "requirement"
				? (route.parts[1] ?? effort?.effort ?? null)
				: (effort?.effort ?? polling.selectedEffort ?? null);
		const view = efforts.find((row) => row.effort === effortName);
		const phaseSubject =
			routePhase(route, efforts)?.phase.subject ??
			(view ? defaultPhase(view) : null);
		const phaseName =
			target?.kind === "requirement"
				? (route.parts[2] ?? phaseSubject)
				: phaseSubject;
		return linkContext(effortName, phaseName, this.detailPayload);
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
		return detailView(this.target.kind, this.detailPayload);
	});

	reset() {
		this.detailPayload = null;
		this.detailError = "";
		this.detailLoading = false;
		this.cancelConfirm();
		this.writeError = "";
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
