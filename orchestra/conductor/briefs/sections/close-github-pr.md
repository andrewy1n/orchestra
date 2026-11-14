## Close

Close is the last phase-end step. It runs after the human merges the PR.
Run `orchestra close --phase {phase}` from the main checkout, not
from a worktree that close removes. Close reads the landing record and
asks `gh` for the PR state. It acts only when the PR is merged. Exit 0
means close finished, found nothing left to do, or found the PR still
open. Exit 1 means close refused and named the path or branch: fix it,
then run close again. Exit 2 means a usage, store or `gh` error.

Close removes each task worktree `<repo>/.worktrees/{phase}--<task-slug>`
and then the phase worktree. It deletes each `task/{phase}/<task-slug>`
branch that is contained in the phase branch and then the
`phase/{phase}` branch. It also updates the effort position, closes
the phase position, and marks the phase done. It skips each step already
done. Plan the next phase only after close.

Session start runs `orchestra close --all`, so a merge between sessions
closes on its own. A session that starts inside a worktree that close
would remove gets a refusal instead.

`orchestra close` needs the `github-pr` adapter and an authenticated
`gh`. Another adapter needs its own close step.
