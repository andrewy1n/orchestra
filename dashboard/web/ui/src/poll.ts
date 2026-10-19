import { getJson } from "./api";
import type { Snapshot } from "./types";
import { TOKEN_POLL_MS } from "./types";

export interface TokenPoller {
  /** Last token value applied to a snapshot load. */
  token: string;
  /** Stop the interval. */
  stop: () => void;
}

export interface TokenPollerOptions {
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

/**
 * Load the snapshot once, then poll `/api/token` on an interval and
 * request `/api/snapshot` again only when the token value changes.
 */
export function startTokenPoller(options: TokenPollerOptions): TokenPoller {
  const intervalMs = options.intervalMs ?? TOKEN_POLL_MS;
  const getToken =
    options.getToken ?? (() => getJson<{ token: string }>("token"));
  const getSnapshot =
    options.getSnapshot ?? (() => getJson<Snapshot>("snapshot"));

  const state: TokenPoller = { token: "", stop: () => {} };
  let timer: ReturnType<typeof setInterval> | undefined;
  let stopped = false;

  async function loadSnapshot(): Promise<void> {
    const snapshot = await getSnapshot();
    if (stopped) return;
    state.token = snapshot.token;
    options.onSnapshot(snapshot);
  }

  async function poll(): Promise<void> {
    try {
      const data = await getToken();
      if (stopped) return;
      if (data.token !== state.token) {
        await loadSnapshot();
      }
    } catch (err) {
      options.onError?.(err instanceof Error ? err.message : String(err));
    }
  }

  // Kick off initial load, then start the interval.
  void (async () => {
    try {
      await loadSnapshot();
    } catch (err) {
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
    if (timer !== undefined) clearInterval(timer);
  };

  return state;
}
