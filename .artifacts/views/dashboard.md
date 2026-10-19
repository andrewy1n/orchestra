# Project Dashboard

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:e1c6a6a3e77728184a48d8fa6300c5e31ac83aae9deeae6fc2af1a76127c562b

## dashboard

### Goal
- **dashboard**: goal: A live terminal dashboard, openable from tmux, shows each effort's phases, tasks and what needs you, lets you move from any item to its related records, and works correctly in every state; scope: effort; kind: deliver _(id: [rec-39db526b-abbb-4753-b9ff-40b8c05662c2](.artifacts/records/project__active-goal/rec-39db526b-abbb-4753-b9ff-40b8c05662c2.md))_

### Phase
- **web-dashboard**: title: Web dashboard; ordinal: 31 _(id: [rec-3c679f20-d25f-4448-9d59-6f2b35a94c32](.artifacts/records/project__phase/rec-3c679f20-d25f-4448-9d59-6f2b35a94c32.md))_

### Ready
- **web-read-api**: title: Serve the read API from dashboard.model; phase: web-dashboard _(id: [rec-f81c5962-37e5-452a-b480-aa4da206b58a](.artifacts/records/project__work-item/rec-f81c5962-37e5-452a-b480-aa4da206b58a.md))_
- **web-ui-scaffold**: title: Scaffold the Vite Svelte app; phase: web-dashboard _(id: [rec-1c76e77e-3b91-444f-a57e-ca02ee31d3eb](.artifacts/records/project__work-item/rec-1c76e77e-3b91-444f-a57e-ca02ee31d3eb.md))_

### Waiting
- **verify-web-dashboard**: title: Verify the web dashboard; phase: web-dashboard _(id: [rec-db6cd2f0-8da1-4f62-a933-f01076471169](.artifacts/records/project__work-item/rec-db6cd2f0-8da1-4f62-a933-f01076471169.md))_
- **web-launcher**: title: Launch the server on loopback for the resolved store; phase: web-dashboard _(id: [rec-6dee2920-ed43-410c-af60-b7cf452aed32](.artifacts/records/project__work-item/rec-6dee2920-ed43-410c-af60-b7cf452aed32.md))_
- **web-ui-actions**: title: Confirm writes and show dismiss errors; phase: web-dashboard _(id: [rec-5d3720ed-eedb-498e-b9c2-ab6af5b9f8b1](.artifacts/records/project__work-item/rec-5d3720ed-eedb-498e-b9c2-ab6af5b9f8b1.md))_
- **web-ui-detail**: title: Open phase, task, requirement, record, and item details; phase: web-dashboard _(id: [rec-866d19de-9eca-443d-bc24-17cb15dbcdc4](.artifacts/records/project__work-item/rec-866d19de-9eca-443d-bc24-17cb15dbcdc4.md))_
- **web-ui-main**: title: Render the rail, goal, phases, and task rows; phase: web-dashboard _(id: [rec-7102f038-1cb1-4752-99f1-2ed73eec9f25](.artifacts/records/project__work-item/rec-7102f038-1cb1-4752-99f1-2ed73eec9f25.md))_
- **web-ui-side**: title: Show Needs you, journal, and backlog; phase: web-dashboard _(id: [rec-a6a8056f-9dee-4efb-a387-c15e653a75be](.artifacts/records/project__work-item/rec-a6a8056f-9dee-4efb-a387-c15e653a75be.md))_
- **web-write-api**: title: Write Needs you and backlog through the existing helpers; phase: web-dashboard _(id: [rec-4474072a-2ef4-487a-afd8-73d4482094c2](.artifacts/records/project__work-item/rec-4474072a-2ef4-487a-afd8-73d4482094c2.md))_

## packaging

### Goal
- **packaging**: goal: se-workflow and adaptive-artifacts install as versioned plugins with declared dependencies, stable plugin-root paths, a single CLI surface for skills, and compatible version checks; scope: effort; kind: deliver _(id: [rec-70873c29-d0a4-4d9a-94d9-aae8ca62cadc](.artifacts/records/project__active-goal/rec-70873c29-d0a4-4d9a-94d9-aae8ca62cadc.md))_

### Needs Human
- **review-cli-package-invariant-violation**: claim: invariant-violation on cli-package: skills still call orchestra.reviewer, orchestra.suite, and orchestra.aa module APIs that the CLI does not expose, contradicting the 'CLI is the only runtime surface' invariant; needs: human _(id: [rec-615efcde-152c-4962-8a78-f8c4253e298b](.artifacts/records/project__finding/rec-615efcde-152c-4962-8a78-f8c4253e298b.md))_
- **review-native-adapters-behavior-bug**: claim: behavior-bug on native-adapters: the Claude hook payload is written to .claude/hooks/hooks.json, which Claude does not read, so R12 is proven only by file presence; needs: human _(id: [rec-4cbc622d-ceab-413d-9a05-a25d149589a3](.artifacts/records/project__finding/rec-4cbc622d-ceab-413d-9a05-a25d149589a3.md))_
- **review2-npx-list-test**: claim: missing-test on the phase exit criterion: no test or installer path exercises `npx skills add --list` resolving a generic profile, as the specification requires; needs: human _(id: [rec-900eee65-bdef-4094-8e48-b994df91b105](.artifacts/records/project__finding/rec-900eee65-bdef-4094-8e48-b994df91b105.md))_
- **review2-opencode-permission-action**: claim: behavior-bug (partly incorrect) on native-adapters: the generated OpenCode agent uses the correct plural permissions key, but also emits an inert write: deny action; write/apply_patch are gated by edit, which is already denied; needs: human _(id: [rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b](.artifacts/records/project__finding/rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b.md))_
- **review2-opencode-plugin-path**: claim: behavior-bug on native-adapters: the OpenCode hook payload is installed at the install root as plugin.js, but OpenCode auto-loads plugins only from <root>/plugins/ (or a plugins config entry), so hook-start/hook-stop never run; needs: human _(id: [rec-265b5127-b459-474e-ab45-732925c68473](.artifacts/records/project__finding/rec-265b5127-b459-474e-ab45-732925c68473.md))_

### Done Recent
- **cli-package**: title: Package orchestra as a console script with contract, project-field, and sessions; phase: cross-harness-install _(id: [rec-404191ec-5110-4b35-ad36-c2f90cdb7e17](.artifacts/records/project__work-item/rec-404191ec-5110-4b35-ad36-c2f90cdb7e17.md))_
- **fix-cli-runtime-surface**: title: Expose reviewer, suite, and store calls through the CLI; phase: cross-harness-install _(id: [rec-23ab51a4-5e9e-42d4-952e-7b04c3659111](.artifacts/records/project__work-item/rec-23ab51a4-5e9e-42d4-952e-7b04c3659111.md))_
- **fix-cli-standalone**: title: Make the installed CLI independent of the affidavit checkout; phase: cross-harness-install _(id: [rec-d825061c-25bf-439f-ac58-c7c222a9f26c](.artifacts/records/project__work-item/rec-d825061c-25bf-439f-ac58-c7c222a9f26c.md))_
- **fix-docs-and-hooks**: title: Update stale install docs and install Claude hooks where Claude reads them; phase: cross-harness-install _(id: [rec-05c7d1c6-19ef-4b36-ac06-be5c55d1a281](.artifacts/records/project__work-item/rec-05c7d1c6-19ef-4b36-ac06-be5c55d1a281.md))_
- **fix-opencode-shape**: title: Install OpenCode plugins where OpenCode reads them and clean the agent permissions; phase: cross-harness-install _(id: [rec-c72fba21-f367-4bb4-9f6c-0da76be3535c](.artifacts/records/project__work-item/rec-c72fba21-f367-4bb4-9f6c-0da76be3535c.md))_
- **fix-reviewer-selfcontainment**: title: Make the reviewer prompt self-contained and single-sourced; phase: cross-harness-install _(id: [rec-ab13b15a-06ee-466d-b27e-f0b271628a49](.artifacts/records/project__work-item/rec-ab13b15a-06ee-466d-b27e-f0b271628a49.md))_
- **install-docs**: title: Document the host matrix and install commands; phase: cross-harness-install _(id: [rec-5bece1b7-9b33-4f9f-8caf-3cdb9f1dee20](.artifacts/records/project__work-item/rec-5bece1b7-9b33-4f9f-8caf-3cdb9f1dee20.md))_
- **installer-cli-flags**: title: Wire wizard, defaults, scope, and list flags; phase: installer-wizard _(id: [rec-4abb30e0-18c9-4bfe-8890-8e5eb9c567ad](.artifacts/records/project__work-item/rec-4abb30e0-18c9-4bfe-8890-8e5eb9c567ad.md))_
- **installer-core**: title: Installer with provider matrix, flags, idempotency, and copy allowlist; phase: cross-harness-install _(id: [rec-42493a4d-650b-410a-a2db-c66590b1ec44](.artifacts/records/project__work-item/rec-42493a4d-650b-410a-a2db-c66590b1ec44.md))_
- **installer-detect**: title: Detect project and global host footprints; phase: installer-wizard _(id: [rec-318f064d-5720-4a51-ad74-2a826498ac0d](.artifacts/records/project__work-item/rec-318f064d-5720-4a51-ad74-2a826498ac0d.md))_
- **installer-docs**: title: Document the installer wizard and detection; phase: installer-wizard _(id: [rec-aee08b08-538c-477b-8de4-1ca7552f1d26](.artifacts/records/project__work-item/rec-aee08b08-538c-477b-8de4-1ca7552f1d26.md))_
- **installer-wizard-primitives**: title: Host, scope, and mode prompts; phase: installer-wizard _(id: [rec-62edc324-8c7c-4a02-9903-b45dbeaa68ab](.artifacts/records/project__work-item/rec-62edc324-8c7c-4a02-9903-b45dbeaa68ab.md))_
- **native-adapters**: title: Native Claude, Cursor, and OpenCode adapters plus the skills-CLI tail; phase: cross-harness-install _(id: [rec-7d73bd37-c7a9-464d-a75d-eb8fb9b94b47](.artifacts/records/project__work-item/rec-7d73bd37-c7a9-464d-a75d-eb8fb9b94b47.md))_
- **portable-skill-refs**: title: Generate per-skill references and prove portability; phase: cross-harness-install _(id: [rec-2e3c03f7-cf51-4d4c-971f-669d1aef11c6](.artifacts/records/project__work-item/rec-2e3c03f7-cf51-4d4c-971f-669d1aef11c6.md))_
- **verify-cross-harness-install**: title: Verify the portable core and harness installer; phase: cross-harness-install _(id: [rec-166cf3ac-bb44-4dd3-8142-fe9618ba0f4d](.artifacts/records/project__work-item/rec-166cf3ac-bb44-4dd3-8142-fe9618ba0f4d.md))_
- **verify-installer-wizard**: title: Verify the installer wizard and detection; phase: installer-wizard _(id: [rec-3b95f2f8-d059-4968-aefb-0d832e8705ac](.artifacts/records/project__work-item/rec-3b95f2f8-d059-4968-aefb-0d832e8705ac.md))_

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
- **proof-dashboard-ui**: title: Show proof packet on dashboard phase detail; phase: phase-proof-packet _(id: [rec-f14cfbd6-c3df-469a-9ac1-aea71336bee5](.artifacts/records/project__work-item/rec-f14cfbd6-c3df-469a-9ac1-aea71336bee5.md))_
- **proof-packet-contract**: title: Add proof-packet type and handoff latest-proof; phase: phase-proof-packet _(id: [rec-149d0a17-eb50-42bf-9b4b-27a94eaabd46](.artifacts/records/project__work-item/rec-149d0a17-eb50-42bf-9b4b-27a94eaabd46.md))_
- **proof-skills-execute**: title: Assemble proof-packet in execute-phase; phase: phase-proof-packet _(id: [rec-fe43d7d2-987e-4f95-9b00-7231755cd0e8](.artifacts/records/project__work-item/rec-fe43d7d2-987e-4f95-9b00-7231755cd0e8.md))_
- **proof-skills-settle-plan**: title: Require ## Proof in settle-phase and plan-phase; phase: phase-proof-packet _(id: [rec-1192d2ed-1e0a-47df-a359-ff748a2a34f1](.artifacts/records/project__work-item/rec-1192d2ed-1e0a-47df-a359-ff748a2a34f1.md))_
- **verify-phase-proof-packet**: title: Verify phase-proof-packet; phase: phase-proof-packet _(id: [rec-1573610a-bad4-4ca7-aab2-b740cf95e974](.artifacts/records/project__work-item/rec-1573610a-bad4-4ca7-aab2-b740cf95e974.md))_
