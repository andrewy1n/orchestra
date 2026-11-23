# dashboard/frontend

The browser dashboard for orchestra: a Vite + Svelte 5 + TypeScript + Tailwind
single-page app. It renders the JSON served by the FastAPI server in
`dashboard/backend/server/` (`GET /api/snapshot`, `POST /api/needs`, `POST /api/backlog`).

## Commands

```
npm ci             # install locked dependencies
npm run dev        # Vite dev server on 127.0.0.1, proxying /api to FastAPI
npm run build      # production build into dist/ (served by dashboard/bin/web)
npm run lint       # Biome
npm test           # vitest
npm run check      # svelte-check, tsc, and generated API type check
npm run e2e        # Playwright
```

## Notes

- The dev server (`server.proxy` in `vite.config.ts`) forwards `/api` to the
  FastAPI server at `http://127.0.0.1:8765`; override with
  `DASHBOARD_API_TARGET`. Same-origin means the API never sends CORS headers.
- Deep links open task details at `#/task/<id>` and phase details at
  `#/phase/<effort>/<phase>`.
- Before running Playwright locally, install Chromium with
  `npx playwright install --with-deps chromium`. Build the frontend first.

## Cursor Cloud

From the repo root, run `UV_PYTHON=3.10 uv sync --locked --group dev`.
Run `npm ci` here with Node 22 to match CI. The cloud boot starts
`dashboard/bin/web --port 8765` and Vite on port 5173. Both listen on
`127.0.0.1`. The API always uses loopback and ignores `--host`.
Use `uv run canon` and `uv run orchestra` for commands from the checkout.
