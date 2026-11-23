# Design

These decisions explain how the current implementation handles progress, evidence,
and external effects. See [Architecture](ARCHITECTURE.md) for the module map.

## Persist the plan and evidence, derive progress on read

A `score:run` records the selected phases and requested steps. Canon also stores
reviews, check-runs, and lifecycle transitions such as a work-item becoming `done`.
Conductor computes the current stage from those records and Git. A fresh session can
resume from recorded outcomes, and the dashboard can explain why a phase is waiting
even if Git changes between agent sessions. [Run records](orchestra/conductor/workflow.py) · [Progress assessment](orchestra/conductor/phase_progress.py)

**Trade-off.** A progress read can require both Canon and Git lookups. A cache tied
only to the store can miss a branch or base ref change. The dashboard keys its
progress cache on the Canon token and the relevant Git refs. [Dashboard cache](dashboard/backend/stages.py)

## Bind approvals and evidence to the inputs they cover

Score checks an approval against the reviewed artifact, its inputs, and its upstream
reviews. Conductor selects evidence for the acceptance and code revision being
evaluated. These checks let an agent resume after a plan or checkout changes while
preserving a record of what previously passed. [Approval checks](orchestra/score/workflow_reviews.py) · [Evidence selection](orchestra/conductor/head_evidence.py)

**Trade-off.** A previously passing check can stop counting. For example, changing
an acceptance's verification command requires a fresh run even at the same Git
commit. An edit to an approved spec can also make downstream reviews stale. The
tests cover both cases. [Command change](tests/conductor/test_check.py) · [Upstream review change](tests/test_workflow_reviews.py)

## Put the shared decision between data collection and presentation

`phase_facts()` gathers approval, execution, and Git facts. `assess(facts)` turns
them into a `PhaseProgress` without I/O. The dashboard displays the result, and the
workflow uses it along with run-specific rules to offer an action. A new rule about
the current stage belongs in the assessment. A rule about which actions the run can
offer belongs in the workflow. [Assessment](orchestra/conductor/phase_progress.py) · [Action selection](orchestra/conductor/workflow.py)

**Trade-off.** `PhaseFacts` grows when a decision needs a new observation. The
explicit input lets a test describe the relevant condition in isolation. For
example, the phase model tests can make a plan incomplete and assert the exact
stage and reason without creating a store or worktree. [Phase model tests](tests/test_phase_progress_model.py)

## Use objects for shared context and replaceable behavior

`Project` binds record operations to one store. `EvidenceIndex` serves repeated
lookups over one record snapshot. Their instances give the context a clear owner
and lifetime. Functions such as `assess(facts)` work with self-contained inputs.
[Project](orchestra/canon/project.py) · [Evidence index](orchestra/conductor/head_evidence.py)

**Trade-off.** An adapter contract adds a layer between an operation and its
implementation. `LandAdapter` earns that layer by supporting configured landing
implementations. `land_phase()` checks the gate, selects the proof, and records the
outcome. The GitHub adapter handles the provider interaction. The landing tests
exercise the operation with a supplied client and check that a failed gate stops
before dispatch. [Landing operation and adapter contract](orchestra/conductor/land.py) · [Landing tests](tests/conductor/test_land_sequence.py)

When a change affects a boundary, a persisted contract, or an example in Concepts,
Architecture, or Design, update the relevant passage in the same PR.
