# Brief: se-reviewer-agent

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### se-reviewer-agent
**title**: Ship read-only se-reviewer agent file; **phase**: phase-reviewer; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Ship `agents/se-reviewer.md` with tool restrictions (Read/Grep/Glob/Bash only; no Write/Edit; prompt forbids mutating commands and store writes) and the structured PASS/NEEDS_WORK output schema from the design. Install copies it via `sync-plugin.sh`. Document the Cursor equivalent (tightest available restriction + prompt forbid) in the agent file or execute-phase.

## Approach

1. Add `agents/se-reviewer.md` with restricted tools, input contract (specs/acceptances/invariants/diff only), and structured output (`verdict`, `findings`, `integration`).
2. Update `scripts/sync-plugin.sh` to copy `agents/` into the plugin install.
3. Note Cursor fallback when hard tool block is unavailable. Do not wire execute-phase invocation here.

## Acceptance Criteria

### se-reviewer-agent
**criterion**: agents/se-reviewer.md exists without Write/Edit tools and forbids store writes; sync-plugin.sh installs the agents/ directory; **method**: check; **effort**: workflow-loop; **verify_command**: test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -f "$d/p/agents/se-reviewer.md"; state: active

## Findings

_None._

## Constraints

_None._

## Position

### phase-reviewer
**position**: executing wave 1: se-reviewer-agent + reviewer-brief; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop done; next up: phase-reviewer; **scope**: effort; state: active

## Unapplied Amendments

_None._
