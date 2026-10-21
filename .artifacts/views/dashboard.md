# Project Dashboard

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:3257c21bf2c00a28ba12b07fbfe696989b230c3142bc83b24c85c67581fa60b1

## dashboard

### Goal
- **dashboard**: goal: A live terminal dashboard, openable from tmux, shows each effort's phases, tasks and what needs you, lets you move from any item to its related records, and works correctly in every state; scope: effort; kind: deliver _(id: [rec-39db526b-abbb-4753-b9ff-40b8c05662c2](.artifacts/records/project__active-goal/rec-39db526b-abbb-4753-b9ff-40b8c05662c2.md))_

### Done Recent
- **verify-web-write-body**: title: Verify web writes read the JSON body; phase: web-write-body _(id: [rec-a0978f37-7118-4aa7-995f-a2d91374a422](.artifacts/records/project__work-item/rec-a0978f37-7118-4aa7-995f-a2d91374a422.md))_
- **web-write-annotations**: title: Drop postponed annotations; phase: web-write-body _(id: [rec-136288f4-1f46-4d85-95ef-52f653278e5d](.artifacts/records/project__work-item/rec-136288f4-1f46-4d85-95ef-52f653278e5d.md))_

## packaging

### Goal
- **packaging**: goal: se-workflow and adaptive-artifacts install as versioned plugins with declared dependencies, stable plugin-root paths, a single CLI surface for skills, and compatible version checks; scope: effort; kind: deliver _(id: [rec-70873c29-d0a4-4d9a-94d9-aae8ca62cadc](.artifacts/records/project__active-goal/rec-70873c29-d0a4-4d9a-94d9-aae8ca62cadc.md))_

### Needs Human
- **review-cli-package-invariant-violation**: claim: invariant-violation on cli-package: skills still call orchestra.reviewer, orchestra.suite, and orchestra.aa module APIs that the CLI does not expose, contradicting the 'CLI is the only runtime surface' invariant; needs: human _(id: [rec-615efcde-152c-4962-8a78-f8c4253e298b](.artifacts/records/project__finding/rec-615efcde-152c-4962-8a78-f8c4253e298b.md))_
- **review-native-adapters-behavior-bug**: claim: behavior-bug on native-adapters: the Claude hook payload is written to .claude/hooks/hooks.json, which Claude does not read, so R12 is proven only by file presence; needs: human _(id: [rec-4cbc622d-ceab-413d-9a05-a25d149589a3](.artifacts/records/project__finding/rec-4cbc622d-ceab-413d-9a05-a25d149589a3.md))_
- **review2-npx-list-test**: claim: missing-test on the phase exit criterion: no test or installer path exercises `npx skills add --list` resolving a generic profile, as the specification requires; needs: human _(id: [rec-900eee65-bdef-4094-8e48-b994df91b105](.artifacts/records/project__finding/rec-900eee65-bdef-4094-8e48-b994df91b105.md))_
- **review2-opencode-permission-action**: claim: behavior-bug (partly incorrect) on native-adapters: the generated OpenCode agent uses the correct plural permissions key, but also emits an inert write: deny action; write/apply_patch are gated by edit, which is already denied; needs: human _(id: [rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b](.artifacts/records/project__finding/rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b.md))_
- **review2-opencode-plugin-path**: claim: behavior-bug on native-adapters: the OpenCode hook payload is installed at the install root as plugin.js, but OpenCode auto-loads plugins only from <root>/plugins/ (or a plugins config entry), so hook-start/hook-stop never run; needs: human _(id: [rec-265b5127-b459-474e-ab45-732925c68473](.artifacts/records/project__finding/rec-265b5127-b459-474e-ab45-732925c68473.md))_

## session-analysis

### Goal
- **session-analysis**: goal: One command aggregates Claude Code transcripts and se-workflow artifact records across sessions, and a skill proposes evidence-backed edits to se-workflow and adaptive-artifacts.; scope: repo; kind: deliver _(id: [rec-ad4c0def-1d0c-4d40-b4d6-48d9d4b0c011](.artifacts/records/project__active-goal/rec-ad4c0def-1d0c-4d40-b4d6-48d9d4b0c011.md))_

## test-suite-speed

### Goal
- **test-suite-speed**: goal: The full test suite runs much faster without adding CPU load; scope: effort; kind: incidental _(id: [rec-6d9a848c-b4a7-4bfd-ac0c-45187ea8180f](.artifacts/records/project__active-goal/rec-6d9a848c-b4a7-4bfd-ac0c-45187ea8180f.md))_

## workflow-loop

### Goal
- **workflow-loop**: goal: The se-workflow loop maps efforts to product areas, closes finished efforts, runs phases in parallel, and settles the approach with the user before planning; scope: effort; kind: deliver _(id: [rec-65213e61-dda6-4955-95bc-8c9c4b289af1](.artifacts/records/project__active-goal/rec-65213e61-dda6-4955-95bc-8c9c4b289af1.md))_

### Done Recent
- **phase-end-cleanup**: title: Remove task worktrees at phase close; phase: task-worktrees _(id: [rec-9d76cc70-508c-479c-92ea-d1340a6c0651](.artifacts/records/project__work-item/rec-9d76cc70-508c-479c-92ea-d1340a6c0651.md))_
- **skill-task-worktree**: title: Dispatch each task in its own worktree; phase: task-worktrees _(id: [rec-2a3f7e8d-81cb-40f8-9703-9db236411e4f](.artifacts/records/project__work-item/rec-2a3f7e8d-81cb-40f8-9703-9db236411e4f.md))_
- **verify-task-worktrees**: title: Verify task worktrees; phase: task-worktrees _(id: [rec-838b8715-ca2d-4c01-a064-b99dd6e66a47](.artifacts/records/project__work-item/rec-838b8715-ca2d-4c01-a064-b99dd6e66a47.md))_
