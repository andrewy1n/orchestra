# dashboard/frontend

The browser dashboard for orchestra: a Vite + Svelte 5 + TypeScript + Tailwind
single-page app. It renders the JSON served by the FastAPI server in
`dashboard/backend/server/` (`GET /api/snapshot`, `POST /api/needs`, `POST /api/backlog`).

## Commands

```
npm install        # install dependencies
npm run dev        # Vite dev server on 127.0.0.1, proxying /api to FastAPI
npm run build      # production build into dist/ (served by dashboard/bin/web)
npm test           # vitest
npm run check      # svelte-check + tsc
```

## Notes

- The dev server (`server.proxy` in `vite.config.ts`) forwards `/api` to the
  FastAPI server at `http://127.0.0.1:8765`; override with
  `DASHBOARD_API_TARGET`. Same-origin means the API never sends CORS headers.
- The theme is light on a fresh load. The top-bar control toggles the `dark`
  class (and `data-theme` token set) on `<html>`, following the design spike in
  `spikes/web-dashboard/`.
- Hash routes (`#/task/...`, `#/phase/...`) render an empty shell for now; the
  scaffold owns the shell, and later screens fill it in.
