# Project Dashboard

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:fc0e33398bc8bf3264bf13d1a0d40b5da6be0df755235ece3c34049b88274484

## dashboard

### Goal
- **dashboard**: goal: A live terminal dashboard, openable from tmux, shows each effort's phases, tasks and what needs you, lets you move from any item to its related records, and works correctly in every state; scope: effort; kind: deliver _(id: [rec-39db526b-abbb-4753-b9ff-40b8c05662c2](.artifacts/records/project__active-goal/rec-39db526b-abbb-4753-b9ff-40b8c05662c2.md))_

### Done Recent
- **deep-links-resolve**: title: Reference resolve helper; phase: deep-links _(id: [rec-966f0550-8372-4227-827a-84c4aecb5634](.artifacts/records/project__work-item/rec-966f0550-8372-4227-827a-84c4aecb5634.md))_
- **deep-links-wire**: title: Wire linkify into meta and markdown; phase: deep-links _(id: [rec-a0c9fa27-5d8a-4f8d-9de6-175ffed667a8](.artifacts/records/project__work-item/rec-a0c9fa27-5d8a-4f8d-9de6-175ffed667a8.md))_
- **milestone-nav-helpers**: title: Milestone grouping and expand helpers; phase: milestone-nav _(id: [rec-6d3e248d-13a3-46fd-b113-d36c911b2d3d](.artifacts/records/project__work-item/rec-6d3e248d-13a3-46fd-b113-d36c911b2d3d.md))_
- **milestone-nav-ui**: title: Phases block UI in App; phase: milestone-nav _(id: [rec-a18ab51a-b527-4d5b-b647-6914c61aa744](.artifacts/records/project__work-item/rec-a18ab51a-b527-4d5b-b647-6914c61aa744.md))_
- **phase-overview-chrome**: title: Shared phase overlay chrome; phase: phase-overview _(id: [rec-6b110034-ce0c-448d-bc27-dbcc1be4425b](.artifacts/records/project__work-item/rec-6b110034-ce0c-448d-bc27-dbcc1be4425b.md))_
- **phase-overview-tabs**: title: Structured UI for each phase tab body; phase: phase-overview _(id: [rec-47538406-49a8-47d0-b170-f7ed18948d13](.artifacts/records/project__work-item/rec-47538406-49a8-47d0-b170-f7ed18948d13.md))_
- **side-rail-home**: title: Calm home side rail; phase: side-rail-calm _(id: [rec-d579406f-4381-42ef-84cb-89e61d7fd9a0](.artifacts/records/project__work-item/rec-d579406f-4381-42ef-84cb-89e61d7fd9a0.md))_
- **side-rail-journal-screen**: title: Journal hash screen; phase: side-rail-calm _(id: [rec-1f9c0953-e991-4014-a53c-e6f479c3f10e](.artifacts/records/project__work-item/rec-1f9c0953-e991-4014-a53c-e6f479c3f10e.md))_
- **task-graph-depends**: title: Enrich task JSON with depends_on ids; phase: task-graph _(id: [rec-56d2c4ac-3566-4c2b-bbaa-f1f0c38176a5](.artifacts/records/project__work-item/rec-56d2c4ac-3566-4c2b-bbaa-f1f0c38176a5.md))_
- **task-graph-ui**: title: Wave-lane dependency graph on Overview; phase: task-graph _(id: [rec-4d4a1801-60f6-47e0-b8b0-047877b88511](.artifacts/records/project__work-item/rec-4d4a1801-60f6-47e0-b8b0-047877b88511.md))_
- **verify-deep-links**: title: Verify deep links; phase: deep-links _(id: [rec-750cba61-f182-42ff-9b69-52b3c1c33f8e](.artifacts/records/project__work-item/rec-750cba61-f182-42ff-9b69-52b3c1c33f8e.md))_
- **verify-milestone-nav**: title: Verify milestone-nav; phase: milestone-nav _(id: [rec-e84c286f-6ece-4473-8270-ccb055ab5f7f](.artifacts/records/project__work-item/rec-e84c286f-6ece-4473-8270-ccb055ab5f7f.md))_
- **verify-phase-overview**: title: Verify phase overview UI; phase: phase-overview _(id: [rec-77db5630-4a2c-443e-8116-a93b4aa8a59b](.artifacts/records/project__work-item/rec-77db5630-4a2c-443e-8116-a93b4aa8a59b.md))_
- **verify-side-rail-calm**: title: Verify side-rail-calm; phase: side-rail-calm _(id: [rec-e927e857-0fd7-4add-b2fa-1389bc237e7d](.artifacts/records/project__work-item/rec-e927e857-0fd7-4add-b2fa-1389bc237e7d.md))_
- **verify-task-graph**: title: Verify task dependency graph; phase: task-graph _(id: [rec-0b8b80f0-2129-4e01-ab35-183edd7ebb0f](.artifacts/records/project__work-item/rec-0b8b80f0-2129-4e01-ab35-183edd7ebb0f.md))_
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
