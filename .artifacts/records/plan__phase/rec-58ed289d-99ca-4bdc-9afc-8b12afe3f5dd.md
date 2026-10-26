---
{
  "id": "rec-58ed289d-99ca-4bdc-9afc-8b12afe3f5dd",
  "lifecycle_state": "done",
  "payload": {
    "effort": "session-analysis",
    "ordinal": 1,
    "title": "Parse transcript JSONL into per-session metrics"
  },
  "record_type": "plan:phase",
  "recorded_at": "2026-10-02T01:42:38+00:00",
  "relationships": {},
  "revision": "sha256:4668d23a2063262096c260cefd0ad0dcd7d958f78837db3b140f64f65e2d1eb6",
  "subject": "transcript-metrics"
}
---

## Problem
Claude Code transcripts are raw JSONL. Nothing turns them into per-session numbers. Each line carries sessionId, timestamp, cwd and gitBranch. Assistant lines hold tool_use blocks. User lines hold tool_result blocks with is_error. cost-state lines hold totalCostUSD.

## Approach
Add scripts/session_metrics.py. It streams each JSONL file, skips and counts bad lines, and ignores unknown fields. It emits one JSON summary per session. Summaries hold counts and references only, never message text. Permission prompts are out of scope here; add them once the transcript signal for them is confirmed.

## Exit criteria
Running the script over ~/.claude/projects emits valid JSON for every session. Each summary has: session id, cwd, branch, start and end time, turn count, tool calls by name, tool errors, retries, cost, skill invocations. A fixture transcript with known counts passes in tests.
