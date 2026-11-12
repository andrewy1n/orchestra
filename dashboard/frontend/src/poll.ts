import { getJson } from "./api";
import type { Snapshot } from "./types";
import { TOKEN_POLL_MS } from "./types";

export interface TokenPoller {
	token: string;
	/** Stop the interval. */
	stop: () => void;
}

export interface TokenPollerOptions {
	fetchSnapshot?: boolean;
	onToken?: (token: string) => void;
	/** Called whenever a fresh snapshot is loaded. */
	onSnapshot: (snapshot: Snapshot) => void;
	/** Called when a poll or load fails. */
	onError?: (message: string) => void;
	/** Interval in ms (defaults to TOKEN_POLL_MS). */
	intervalMs?: number;
	/** Injected fetch helpers for tests. */
	getToken?: () => Promise<{ token: string }>;
	getSnapshot?: () => Promise<Snapshot>;
}

export function startTokenPoller(options: TokenPollerOptions): TokenPoller {
	const intervalMs = options.intervalMs ?? TOKEN_POLL_MS;
	const fetchSnapshot = options.fetchSnapshot ?? true;
	const controller = new AbortController();
	const getToken =
		options.getToken ??
		(() => getJson<{ token: string }>("token", { signal: controller.signal }));
	const getSnapshot =
		options.getSnapshot ??
		(() => getJson<Snapshot>("snapshot", { signal: controller.signal }));

	const state: TokenPoller = { token: "", stop: () => {} };
	let timer: ReturnType<typeof setInterval> | undefined;
	let stopped = false;
	let polling = false;

	async function loadSnapshot(): Promise<void> {
		const snapshot = await getSnapshot();
		if (stopped) return;
		state.token = snapshot.token;
		options.onToken?.(snapshot.token);
		options.onSnapshot(snapshot);
	}

	async function poll(): Promise<void> {
		if (stopped || polling) return;
		polling = true;
		try {
			const data = await getToken();
			if (stopped) return;
			if (data.token !== state.token) {
				if (fetchSnapshot) {
					await loadSnapshot();
				} else {
					state.token = data.token;
					options.onToken?.(data.token);
				}
			}
		} catch (err) {
			if (!stopped)
				options.onError?.(err instanceof Error ? err.message : String(err));
		} finally {
			polling = false;
		}
	}

	void (async () => {
		try {
			if (fetchSnapshot) await loadSnapshot();
			else await poll();
		} catch (err) {
			if (!stopped)
				options.onError?.(err instanceof Error ? err.message : String(err));
		}
		if (!stopped) {
			timer = setInterval(() => {
				void poll();
			}, intervalMs);
		}
	})();

	state.stop = () => {
		stopped = true;
		controller.abort();
		if (timer !== undefined) clearInterval(timer);
	};

	return state;
}
