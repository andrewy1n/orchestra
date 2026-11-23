# Orchestra concepts

Orchestra organizes work around outcomes and keeps the evidence used to judge
whether those outcomes hold.

## Ideas and active work

**Composer** is where proposed work lives. An idea can stay open until someone
chooses to promote it or dismiss it. An area groups work by part of the product,
and a placement associates an effort with an area. Promoting an idea gives it an
effort and can link it to the phase where the work will happen.
[Composer record types](orchestra/composer/schemas/composer.json)

An **effort** is a continuing objective and the focus of a chat. New work within
that objective can form a new phase. A **milestone** can group several phases
around a time-bounded outcome. The dashboard rolls up progress from the member
phases, and the workflow still plans and reviews each phase.
[Effort and phase model](orchestra/conductor/briefs/sections/kinds-and-focus.md)

## What a phase plans

A specification describes the expected behavior. A design describes the approach.
The task plan connects work-items to the requirements they address and gives those
requirements a way to be checked. A step review records which inputs were approved.

```text
Phase
├── Requirement · What must be true
├── Work-item · Work that contributes to a requirement
└── Acceptance · How a requirement is checked
    └── Check-run · The recorded result of one check
```

A light phase keeps the requirements and approach in the phase record. A full
phase gives the specification and design their own records. Both have spec and
design review steps. A one-off that fits in one chat can take the incidental path
with less planning. [Kinds](README.md#kinds) · [Phase review artifacts](orchestra/score/workflow_reviews.py)

## How verification works

A **requirement** describes an observable outcome. An **acceptance** names how to
check it. Orchestra supports three acceptance methods.

| Method | Evidence it calls for |
|---|---|
| `tdd` | A failing test that demonstrates the missing behavior, followed by a passing test. |
| `check` | A passing automated check, such as a build or smoke test. |
| `manual` | Human sign-off. |

Selected automated acceptances can use a **frozen oracle**, which pins the tests
used as evidence. The method describes what results are needed and the oracle
policy describes whether the tests must match the approved version.
[Verification policy](orchestra/conductor/briefs/sections/verification-policy.md)

A check-run records one observation. When Orchestra evaluates a requirement, it
looks for applicable results for its acceptances and the code revision being
evaluated. That is why a requirement can be **unverified** even when a previous
revision passed. For structured work, an **assessment** records what the evidence
means and what should be revisited, such as the implementation or specification.
[Requirement status](orchestra/conductor/requirements.py) · [Lifecycle](README.md#lifecycle)

## When work is done

A work-item can be **done** while the phase is still open. Phase verification
checks the combined work and gathers the configured evidence, such as suite
results and a review. The **phase gate** checks whether landing can proceed. GitHub
landing publishes the phase commit and opens or updates its PR. By default, it
also waits for checks on that commit. A configured merge-evidence adapter evaluates
CI separately. A human merges the PR, and close then marks the phase `done`.
[Phase progress](orchestra/conductor/phase_progress.py) · [GitHub landing](orchestra/conductor/briefs/sections/land-github-pr.md)

## Glossary

| Term | Meaning |
|---|---|
| **Acceptance** | The check used to determine whether a requirement holds. |
| **Area** | A named part of the product used to organize ideas and efforts. |
| **Check-run** | The recorded result of one check, such as `pass` or `fail`. Several check-runs can refer to the same acceptance. |
| **Closed** | The phase has been marked `done`. For a phase landed through GitHub, close follows merge. |
| **Effort** | A continuing objective that can span several phases. |
| **Focus** | The effort the current chat is working on. |
| **Idea** | A proposal that can be organized in the backlog or promoted into work. |
| **Landed** | The landing operation reported success. With GitHub, the phase commit was published to the PR. When landing evaluates CI, success also requires acceptable check results. |
| **Milestone** | An optional grouping of phases within an effort around one time-bounded outcome. |
| **Phase** | A scoped outcome within an effort. Its plan connects requirements to work-items and acceptances. |
| **Placement** | The association between an effort and its product area. |
| **Requirement** | An observable condition that must hold for the phase to meet its outcome. |
| **Verified** | The applicable evidence satisfies the requirement. Phase verification also checks the combined work and the configured gates. |
| **Work-item** | A tracked unit of work, often called a task. Its own lifecycle records when it is planned, in progress, or done. |

See [Architecture](ARCHITECTURE.md) for where these concepts live in the code and
[Design](DESIGN.md) for how Orchestra uses them to make decisions.
