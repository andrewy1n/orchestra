/**
 * API surface for the web dashboard.
 *
 * The page is served by Vite; the JSON lives on the FastAPI server
 * (`dashboard.web`). In development the Vite dev server proxies `/api`
 * (see `vite.config.ts`), so the browser always talks to a same-origin
 * `/api` path and the server never has to send CORS headers.
 */

/** Where the FastAPI server listens during development. */
export const API_TARGET = "http://127.0.0.1:8765";

/** Same-origin prefix the Svelte app codes against. */
export const API_BASE = "/api";

/** Build an `/api` URL for a route such as `snapshot`. */
export function apiUrl(path: string): string {
  const clean = path.replace(/^\/+/, "");
  return clean ? `${API_BASE}/${clean}` : API_BASE;
}

/** GET a JSON document from the API. */
export async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    headers: { accept: "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`GET ${apiUrl(path)} failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

/** POST a JSON body to the API. */
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${apiUrl(path)} failed: ${response.status}`);
  }
  return (await response.json()) as T;
}
