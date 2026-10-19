---
{
  "base_kind": "observation",
  "id": "rec-96725f9c-7a93-4e8b-8677-f53b7a41b3fa",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "fix-opencode-shape",
    "result": "pass",
    "revision": "b473060144dca418b3d6e7fea7e4616461bc1e9a",
    "verdict": "pass",
    "work_item": "fix-opencode-shape"
  },
  "provenance": {
    "sources": [
      "fix-opencode-shape"
    ]
  },
  "record_type": "project:execution-report",
  "recorded_at": "2026-10-19T02:26:03+00:00",
  "relationships": {},
  "revision": "sha256:e6faeebf474fdeb4dbd9fc70cfe3bb5626593c3e33f627fbf5db2e8f5f6456ec",
  "subject": "fix-opencode-shape",
  "time": {
    "observed": "2026-10-19T02:26:03+00:00",
    "recorded": "2026-10-19T02:26:03+00:00"
  }
}
---

subject: fix-opencode-shape
kind: deliver
result: pass
revision: b473060144dca418b3d6e7fea7e4616461bc1e9a
evidence: From worktree `/home/andrewyin/orchestra/.worktrees/cross-harness-install`: `python3 -m pytest tests/test_installer.py tests/integration/test_temp_home_install.py -q -k "opencode or hooks or temp_home"` -> 13 passed, 27 deselected; `python3 -m pytest tests/test_agent_generation.py tests/test_installer.py -q -k "opencode"` -> 4 passed, 46 deselected; full affected files (`test_installer`, `test_temp_home_install`, `test_agent_generation`, `test_readme_matrix`) -> 62 passed. Broader suite blocked by unrelated environment issues (`textual`/`rich` not installed, worktree lacks `.artifacts/project-design.json` and `AGENTS.md`).
observations: OpenCode discovers plugins only under `plugins/`; generated OpenCode frontmatter previously carried an inert `write: deny`, while `edit: deny` is the effective write gate. Legacy root-plugin markers are cleaned on reinstall. README and installer/integration/agent tests now assert `<root>/plugins/plugin.js`, the absence of the old root path, plural `permissions:`, `edit: deny`, and no `write`/`apply_patch` keys. No `npx --list` test was added, per decision `npx-list-clause`.
root_cause: The OpenCode payload was copied with its source-relative flat name, so `plugin.js` landed at the host root; the renderer passed every deny tool through lowercased, emitting `write` separately from `edit`.
verdict: pass
metrics: 1 destination path corrected for project and global scopes; 1 legacy root marker cleaned; 2 inert permission keys removed; 62 affected tests passed.
claim: OpenCode hook plugins install at `<root>/plugins/plugin.js` for project and global scopes, the old root path is absent, and generated OpenCode agents use plural `permissions:` with `edit: deny` and no inert `write`/`apply_patch` keys.
needs_human: false
attempted_action:
retry_when:
blocker:
