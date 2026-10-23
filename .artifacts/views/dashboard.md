# Project Dashboard

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:c32151343ec179e17e4011f54a9599c94a563fc3f1d121c1e534ee94d605de39

## dashboard

### Goal
- **dashboard**: goal: A live terminal dashboard, openable from tmux, shows each effort's phases, tasks and what needs you, lets you move from any item to its related records, and works correctly in every state; scope: effort; kind: deliver _(id: [rec-39db526b-abbb-4753-b9ff-40b8c05662c2](.artifacts/records/project__active-goal/rec-39db526b-abbb-4753-b9ff-40b8c05662c2.md))_

## library-boundary

### Goal
- **library-boundary**: goal: adaptive-artifacts, affidavit, and orchestra call each other in-process through small Python libraries. The commands stay for agents and humans. One function in adaptive-artifacts opens the store. SE_WORKFLOW_STORE is gone.; scope: effort; kind: deliver _(id: [rec-e474e2d8-be06-44e2-8583-27966c04a3b3](.artifacts/records/project__active-goal/rec-e474e2d8-be06-44e2-8583-27966c04a3b3.md))_

### Done Recent
- **claim-gate-clocks**: title: Report verdict and recheck failures together; phase: claim-clocks _(id: [rec-ce44fbe7-37a7-4317-b62b-5faa40332cc1](.artifacts/records/project__work-item/rec-ce44fbe7-37a7-4317-b62b-5faa40332cc1.md))_
- **claim-gate-source**: title: Read the claim id only from payload.claim; phase: claim-clocks _(id: [rec-89c53c0e-9062-45c0-974e-041a5550bb08](.artifacts/records/project__work-item/rec-89c53c0e-9062-45c0-974e-041a5550bb08.md))_
- **fix-claim-gate-e2e**: title: Gate the library e2e oracle and empty-manifest claims; phase: claim-clocks _(id: [rec-7a4b59f7-6d14-46ab-8900-85edde14d269](.artifacts/records/project__work-item/rec-7a4b59f7-6d14-46ab-8900-85edde14d269.md))_
- **fix-claim-gate-regressions**: title: Fix claim gate regressions from the phase changes; phase: claim-clocks _(id: [rec-f56f40a2-4190-4ce4-9a33-ae493f5868e2](.artifacts/records/project__work-item/rec-f56f40a2-4190-4ce4-9a33-ae493f5868e2.md))_
- **fix-claim-gate-unit-hook**: title: Fix claim gate unit-test hook and prove claim_id is ignored; phase: claim-clocks _(id: [rec-b6b10a49-254c-416e-a0d9-4d73be88c567](.artifacts/records/project__work-item/rec-b6b10a49-254c-416e-a0d9-4d73be88c567.md))_
- **verify-claim-clocks**: title: Verify claim-clocks; phase: claim-clocks _(id: [rec-419fa45f-35f6-401e-9ce2-d59417644d68](.artifacts/records/project__work-item/rec-419fa45f-35f6-401e-9ce2-d59417644d68.md))_

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

### Needs Human
- **review-skills-oracle-red-docs**: claim: skills still document affidavit.oracle_red Python API while close-batch is CLI-only; needs: human _(id: [rec-ef1901ba-46da-4daf-a533-cb14f4552b2a](.artifacts/records/project__finding/rec-ef1901ba-46da-4daf-a533-cb14f4552b2a.md))_
