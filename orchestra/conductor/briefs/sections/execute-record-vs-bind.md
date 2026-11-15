## Record versus bind

Techniques and audit may record an unbound evidence-observation. It
does not earn a manifest claim. Path: claim id → evidence-binding →
evidence-observation. `orchestra verify bind` writes the
evidence-binding; then `orchestra verify recheck` before treating the
claim as earned. Inspect with `orchestra verify trail`.

```bash
orchestra verify trail --cwd <repo-or-worktree>
orchestra verify bind --cwd <repo-or-worktree> \
  --observation <evidence-observation-id> \
  --claim <claim-id> --base <base-rev> --head <head-rev>
orchestra verify recheck --cwd <repo-or-worktree> --claim <claim-id>
```
