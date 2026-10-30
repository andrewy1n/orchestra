---
{
  "id": "rec-b5ac09db-6f3d-402b-87b1-3ae7e7407da4",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "agent-shadcn-init",
    "decisions": [
      "shadcn-svelte",
      "shadcn-appearance"
    ],
    "depends_on": [
      "move-frontend"
    ],
    "effort": "dashboard",
    "estimate_minutes": 25,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "ui-structure",
    "requirements": [
      "R6",
      "R7",
      "R9",
      "R10"
    ],
    "size": "L",
    "title": "Set the $lib alias and initialize shadcn-svelte"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T21:41:25+00:00",
  "relationships": {},
  "revision": "sha256:1a3f9ff929e8fdb906290e8f0b84aecf4bea4bd9d4cf1fba631e1bcebfe74f00",
  "subject": "shadcn-init"
}
---

## Description

R6: `components.json` exists and its aliases point at `$lib`.
R7: The `$lib` alias resolves in `vite.config.ts` and in the tsconfig.
R9: The global CSS defines the shadcn theme variables.
R10: `npm run lint` passes with the shadcn components present.
Context: the web UI (Vite + Svelte 5 + TypeScript + Tailwind 4, Biome lint, Vitest) lives at `dashboard/web/ui` with a 1,264-line `src/App.svelte` (613 lines of script). The FastAPI server lives in `dashboard/backend/server/` and serves `dashboard/web/ui/dist`. This phase moves the UI to `dashboard/frontend`, adds the `$lib` alias and shadcn-svelte, splits `App.svelte` into state modules and screens, and adopts the shadcn default look. Behavior, routes, and deep links do not change. The lint gate stays at zero findings. The CI `web` job runs `npm ci`, `npm run lint`, `npm run check`, `npm test`, `npm run build` in the UI folder. `npm run check` also runs `api-types:check`.

## Approach

In `dashboard/frontend`: add the `$lib` alias to `vite.config.ts` (`resolve.alias`) and to `tsconfig.app.json` (`paths`: `$lib` and `$lib/*` to `./src/lib` and `./src/lib/*`); create `src/lib/utils.ts` as shadcn expects. Run `npx shadcn-svelte@latest init` non-interactively for Svelte 5, Tailwind 4, plain Vite (not SvelteKit), with aliases `$lib`, `$lib/components`, `$lib/components/ui`, `$lib/utils`, `$lib/hooks` and the default base color (pass flags; read `npx shadcn-svelte@latest init --help`). Record the CLI version in the commit body. Merge the generated theme variables into `src/app.css` (`:root` and `.dark` variables, `@theme inline`, base layer) and keep the Tailwind imports and every existing rule the UI still needs; the existing `dark` class toggle in `src/theme.ts` keeps working. Add the components the later tasks need: `tabs`, `dialog`, `button`, `badge` (via `npx shadcn-svelte@latest add`). Exclude `src/lib/components/ui` from lint and format in `biome.json` (generated files). Add exact versions for new dependencies. Run `npm run lint`, `npm run check`, `npm test`, `npm run build`: Vitest must still pass before any restyle.
