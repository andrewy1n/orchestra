# Architecture

Agent skills carry out work and record what happened. Canon stores the plan and
evidence, Score and Tuner give those records meaning, and Conductor uses them with
Git state to decide what can happen next. The CLI, session handoff, and dashboard
use those decisions through their own interfaces. See [Design](DESIGN.md) for the
trade-offs and the [boundary tests](tests/test_boundaries.py) for allowed imports.

## Main workflow components

Each arrow points from a caller to the component it uses for the labeled action.

```mermaid
flowchart TD
    CLI["Orchestra CLI"] -->|Dispatches workflow commands| Conductor["Conductor<br/>Workflow and verification"]
    Dashboard["Dashboard backend"] -->|Reads phase progress| Conductor
    Hooks["Stage session hooks"] -->|Read phase progress for handoff| Conductor
    Conductor -->|Reads plans and requirements| Score["Score<br/>Planning records"]
    Conductor -->|Interprets check results| Tuner["Tuner<br/>Verification evidence"]
    Conductor -->|Reads and writes records| Canon["Canon<br/>Record store"]
    Score -->|Decodes planning records| Canon
    Tuner -->|Decodes evidence records| Canon
```

## How Orchestra computes and shares phase progress

```mermaid
flowchart TD
    Store["canon/project.py · records()"] --> Phase["score/planning/phase.py · read_phase()"]
    Store --> Facts["conductor/phases/progress/phase_progress.py · phase_facts()"]
    Phase --> Facts
    Git["tools/git.py · Git state"] --> Facts
    Facts --> Progress["conductor/phases/progress/phase_progress.py · assess() returns PhaseProgress"]
    Progress --> Workflow["conductor/phases/workflow/workflow.py · next action"]
    Progress --> Dashboard["dashboard/backend/stages.py · displayed progress"]
    Progress --> Handoff["stage/hooks.py · session context"]
```

For example, a phase with approved spec and design can stay at `tasks` because its
plan lacks work-items. The phase model test shows how `assess()` picks the first
open stage in this case. [Phase assessment](orchestra/conductor/phases/progress/phase_progress.py) ·
[Phase model test](tests/test_phase_progress_model.py)

## Where to find the code

### Records, planning, and evidence

| Package | Modules to read |
|---|---|
| **Canon** | [`workspace.py`](orchestra/canon/workspace.py) resolves which store to open. [`project.py`](orchestra/canon/project.py) exposes `get()`, `records()`, and record mutations. [`schema.py`](orchestra/canon/schema.py) loads record definitions and [`validation.py`](orchestra/canon/validation.py) checks payloads, references, and transitions. [`backend.py`](orchestra/canon/backend.py) defines the storage contract and [`sqlite_backend.py`](orchestra/canon/sqlite_backend.py) implements it. [`derive.py`](orchestra/canon/derive.py) computes dependency readiness and waves. |
| **Score** | [`phase.py`](orchestra/score/planning/phase.py), [`work_item.py`](orchestra/score/planning/work_item.py), [`acceptance.py`](orchestra/score/planning/acceptance.py), and [`standing_constraint.py`](orchestra/score/planning/standing_constraint.py) read typed planning records. [`requirements.py`](orchestra/score/planning/requirements.py) reads requirement definitions. [`workflow_reviews.py`](orchestra/score/workflow/workflow_reviews.py) checks whether approvals still apply, and [`analyze.py`](orchestra/score/planning/analyze.py) checks plan consistency. |
| **Tuner** | [`records.py`](orchestra/tuner/evidence/records.py) defines `CheckRun`, `Finding`, and `EvidenceBinding`. [`manifest.py`](orchestra/tuner/plugins/manifest.py) loads claims at a Git revision. [`verdict.py`](orchestra/tuner/evidence/verdict.py) evaluates those claims and [`binding.py`](orchestra/tuner/evidence/binding.py) associates observations with them. [`technique.py`](orchestra/tuner/plugins/technique.py) defines the verification plugin interface. |
| **Composer** | [`records.py`](orchestra/composer/records.py) models ideas, areas, and placements. [`idea.py`](orchestra/composer/idea.py) captures ideas, and [`placement.py`](orchestra/composer/placement.py) assigns an effort to an area. |

The [schema registrations](pyproject.toml) point to each package's record types
and lifecycles. Canon validates writes against the store's schema snapshots.

### Workflow decisions in Conductor

| Question | Modules to read |
|---|---|
| **What step is open?** | [`phase_progress.py`](orchestra/conductor/phases/progress/phase_progress.py) gathers `PhaseFacts` and computes `PhaseProgress`. [`workflow.py`](orchestra/conductor/phases/workflow/workflow.py) uses that result, run scope, and blockers to choose an action. [`briefs/render.py`](orchestra/conductor/briefs/render.py) assembles the agent instructions. |
| **Where is approval recorded?** | [`workflow_review.py`](orchestra/conductor/phases/workflow/workflow_review.py) checks authority and records a step review. Score's [`workflow_reviews.py`](orchestra/score/workflow/workflow_reviews.py) evaluates that review when the plan is read. |
| **Why is this task ready or done?** | [`wave.py`](orchestra/conductor/tasks/wave.py) selects and starts ready work. [`task_landing.py`](orchestra/conductor/tasks/task_landing.py) coordinates task landing and closure. [`land_task.py`](orchestra/conductor/tasks/land_task.py) handles the task's code and evidence, and [`task_close.py`](orchestra/conductor/tasks/close/task_close.py) evaluates the conditions for transitioning it to `done`. |
| **Why does this check count?** | [`check.py`](orchestra/conductor/verification/check.py) runs an acceptance command and records a `tuner:check-run`. [`head_evidence.py`](orchestra/conductor/verification/evidence/head_evidence.py) selects eligible check-runs for an acceptance and revision. [`requirements.py`](orchestra/conductor/verification/requirements.py) combines those results into requirement status. |
| **Where does phase-wide evidence come from?** | [`suite.py`](orchestra/conductor/verification/suite/suite.py) handles suite runs and policy. [`reviewer.py`](orchestra/conductor/verification/review/reviewer.py) prepares review inputs and interprets reviewer output. |
| **Why can the phase land?** | [`gate.py`](orchestra/conductor/landing/gate.py) evaluates landing conditions. [`landing.py`](orchestra/conductor/landing/landing.py) reads the worktree location, proof packet, and landing record. [`land.py`](orchestra/conductor/landing/land.py) checks the gate and invokes the adapter. [`github_pr.py`](orchestra/conductor/landing/github_pr.py) handles the GitHub interaction, and [`close.py`](orchestra/conductor/phases/progress/close.py) handles closure after merge. |

### Interfaces and external commands

- **CLI and skills.** [`orchestra/cli.py`](orchestra/cli.py) composes the package commands. [`tools/command_kit.py`](orchestra/tools/command_kit.py) defines command registration, dispatch, and CLI errors. [`conductor/cli/workflow_commands.py`](orchestra/conductor/cli/workflow_commands.py) maps `workflow` commands to Conductor functions. Skills use the briefs those functions render.
- **Terminal and sessions.** [`views/render.py`](orchestra/views/render.py) formats record views. [`stage/hooks.py`](orchestra/stage/hooks.py) assembles session context with [`stage/handoff.py`](orchestra/stage/handoff.py).
- **Dashboard.** [`server/app.py`](dashboard/backend/server/app.py) defines the HTTP routes. [`server/service.py`](dashboard/backend/server/service.py) assembles responses and manages the cache. [`stages.py`](dashboard/backend/stages.py) reads shared phase progress, and [`phase.py`](dashboard/backend/phase.py) builds phase details for the UI.
- **External commands.** [`tools/cli_tool.py`](orchestra/tools/cli_tool.py) provides the process runner. [`tools/git.py`](orchestra/tools/git.py) wraps Git and exposes branch state used by progress and close.
