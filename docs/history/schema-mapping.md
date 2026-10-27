# Schema mapping: project:* to plan, run, aff

Source: `contract/project-design.json` in orchestra (26 types) and affidavit (adds `evidence-observation`).
Lifecycle map: `current-status`, `definition`, `decision` to `current`; `phase`, `task` to `staged`; `event`, `observation`, `instruction` to `event`; `question` to `question`; `finding` to `claim`.
Every field stays under the same name unless a row says otherwise. Fields not listed under a type do not exist in the old contract.

Form changes: `str>list` is a comma-separated string that becomes a list; `str>ref` is a string that becomes a subject reference. Scalar typings (integer, number, boolean) keep the stored value.

## Built-in and dropped fields

- `depends_on` (relationship, ids) becomes built-in `payload.depends_on` (subjects) on staged types: `plan:milestone`, `plan:phase`, `plan:work-item`. It is not declared in the module.
- `supersedes` and `corrects` stay in `relationships`.
- `informed_by` (relationship, ids) becomes declared `informed_by`, a pinned-id list, on `aff:check-run` and `run:failed-attempt` only (the `event` pattern carried the `evidence-linked` trait).
- `contradicted_by` (relationship, ids) becomes declared `contradicted_by`, a pinned-id list, on `plan:decision` (trait `contradictable`) and `aff:finding` (trait `epistemic-claim`).
- The implicit `entity` trait payload field `subject` moves to the envelope `subject`.
- `project:active-goal.scope` is dropped.
- Envelope keys `base_kind`, `identity`, `stewardship`, `epistemic_status` are dropped.

## Types

### project:active-goal -> plan:effort

Pattern `current-status` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `goal` | `goal` | string |
| `scope` | dropped | |
| `kind` | `kind` | string |
| `status` | `status` | enum optional |
| `merged_from` | `merged_from` | list of string optional; str>list (some already lists) |

### project:current-position -> plan:position

Pattern `current-status` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `position` | `position` | string |
| `scope` | `scope` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `phase` | `phase` | ref plan:phase optional; str>ref |
| `status` | `status` | enum optional |

### project:milestone -> plan:milestone

Pattern `phase` -> lifecycle `staged`. Sections: Outcome, Exit criteria.

| Old field | New field | Form |
|---|---|---|
| `title` | `title` | string |
| `ordinal` | `ordinal` | integer |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:phase -> plan:phase

Pattern `phase` -> lifecycle `staged`. Sections: Problem, Approach, Exit criteria.

| Old field | New field | Form |
|---|---|---|
| `title` | `title` | string |
| `ordinal` | `ordinal` | integer |
| `effort` | `effort` | ref plan:effort; str>ref |
| `milestone` | `milestone` | ref plan:milestone optional; str>ref |

### project:work-item -> plan:work-item

Pattern `task` -> lifecycle `staged`. Sections: Description.

| Old field | New field | Form |
|---|---|---|
| `title` | `title` | string |
| `phase` | `phase` | ref plan:phase; str>ref |
| `kind` | `kind` | string |
| `assignee` | `assignee` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `executor` | `executor` | enum optional |
| `requirements` | `requirements` | list of string optional; str>list |
| `decisions` | `decisions` | list of ref plan:decision optional; str>list of refs |
| `size` | `size` | enum optional |
| `estimate_minutes` | `estimate_minutes` | integer optional |
| `attempts` | `attempts` | integer optional |

### project:acceptance -> plan:acceptance

Pattern `definition` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `criterion` | `criterion` | string optional |
| `method` | `method` | enum |
| `phase` | `phase` | ref plan:phase; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| `verify_command` | `verify_command` | string |
| `requirement` | `requirement` | string optional |
| `test_ids` | `test_ids` | list of string optional; str>list |
| `oracle_hashes` | `oracle_hashes` | list of string optional; str>list |

### project:constraint -> plan:constraint

Pattern `definition` -> lifecycle `current`. Sections: Basis.

| Old field | New field | Form |
|---|---|---|
| `statement` | `statement` | string |
| `applies_to` | `applies_to` | string |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:check-run -> aff:check-run

Pattern `event` -> lifecycle `event`.

| Old field | New field | Form |
|---|---|---|
| `criterion_id` | `criterion_id` | string |
| `revision` | `revision` | string |
| `result` | `result` | enum |
| `effort` | `effort` | ref plan:effort; str>ref |
| `method` | `method` | enum |
| `signed_by` | `signed_by` | string |
| `requirement` | `requirement` | string optional |
| `evidence_kind` | `evidence_kind` | enum optional |
| `exit_code` | `exit_code` | integer optional |
| `duration_s` | `duration_s` | number optional |
| `output_sha256` | `output_sha256` | string optional |
| `runner` | `runner` | string optional |
| `diff_sha256` | `diff_sha256` | string optional |
| `failing_node_ids` | `failing_node_ids` | list of string optional; str>list |
| `signed_note` | `signed_note` | string optional |
| (relationship `informed_by`) | `informed_by` | list of ref plan:acceptance|run:execution-report pin optional; relationship to payload field |

### project:decision -> plan:decision

Pattern `decision` -> lifecycle `current`. Sections: Rationale, Counter-argument.

| Old field | New field | Form |
|---|---|---|
| `choice` | `choice` | string |
| `alternatives` | `alternatives` | string |
| `phase` | `phase` | ref plan:phase; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| (relationship `contradicted_by`) | `contradicted_by` | list of ref plan:decision pin optional; relationship to payload field |

### project:continuity-question -> plan:continuity-question

Pattern `question` -> lifecycle `question`.

| Old field | New field | Form |
|---|---|---|
| `owner` | `owner` | string |
| `blocking` | `blocking` | boolean |
| `scope` | `scope` | string |
| `answer` | `answer` | string optional |

### project:failed-attempt -> run:failed-attempt

Pattern `event` -> lifecycle `event`.

| Old field | New field | Form |
|---|---|---|
| `attempted_action` | `attempted_action` | string |
| `retry_when` | `retry_when` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| (relationship `informed_by`) | `informed_by` | list of ref plan:acceptance|run:execution-report pin optional; relationship to payload field |

### project:investigation-observation -> aff:investigation-observation

Pattern `observation` -> lifecycle `event`.

| Old field | New field | Form |
|---|---|---|
| `source` | `source` | string |
| `observed_time` | `observed_time` | string |
| `environment` | `environment` | string |
| `what_was_observed` | `what_was_observed` | string |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:evidence-binding -> aff:evidence-binding

Pattern `current-status` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `observation_id` | `observation_id` | string |
| `claim_id` | `claim_id` | string |
| `base_rev` | `base_rev` | string |
| `head_rev` | `head_rev` | string |
| `effort` | `effort` | ref plan:effort optional; str>ref |

### project:finding -> aff:finding

Pattern `finding` -> lifecycle `claim`. Sections: Evidence, Consequence, Follow-up.

| Old field | New field | Form |
|---|---|---|
| `claim` | `claim` | string |
| `basis` | `basis` | string |
| `invalidated_when` | `invalidated_when` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `needs` | `needs` | string |
| `resolution_note` | `resolution_note` | string optional |
| (relationship `contradicted_by`) | `contradicted_by` | list of ref aff:finding pin optional; relationship to payload field |

### project:assignment -> run:assignment

Pattern `instruction` -> lifecycle `event`. Sections: Orientation.

| Old field | New field | Form |
|---|---|---|
| `work_item` | `work_item` | ref plan:work-item; str>ref |
| `executor` | `executor` | string |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:assignment-amendment -> run:assignment-amendment

Pattern `instruction` -> lifecycle `event`. Sections: Correction.

| Old field | New field | Form |
|---|---|---|
| `assignment` | `assignment` | ref run:assignment; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:execution-report -> run:execution-report

Pattern `observation` -> lifecycle `event`.

| Old field | New field | Form |
|---|---|---|
| `work_item` | `work_item` | ref plan:work-item; str>ref |
| `assignment` | `assignment` | ref run:assignment; str>ref |
| `result` | `result` | string |
| `verdict` | `verdict` | string |
| `revision` | `revision` | string |

### project:specification -> plan:specification

Pattern `definition` -> lifecycle `current`. Sections: Requirements, Acceptance criteria, Constraints, Non-goals, Invariants, Assumptions.

| Old field | New field | Form |
|---|---|---|
| `weight` | `weight` | enum |
| `phase` | `phase` | ref plan:phase; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| `requirements` | `requirements` | list of string; str>list |

### project:design -> plan:design

Pattern `definition` -> lifecycle `current`. Sections: Architecture, Interfaces, Decisions, Invariants, Assumptions, Tradeoffs, Risks.

| Old field | New field | Form |
|---|---|---|
| `phase` | `phase` | ref plan:phase; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| `decisions` | `decisions` | list of ref plan:decision; str>list of refs |

### project:integration-report -> run:integration-report

Pattern `observation` -> lifecycle `event`. Sections: Interfaces, Assumptions, Invariants, Conflicts.

| Old field | New field | Form |
|---|---|---|
| `phase` | `phase` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `result` | `result` | enum |
| `revision` | `revision` | string |

### project:proof-packet -> run:proof-packet

Pattern `observation` -> lifecycle `event`. Sections: Look, Machine, Attention, Diff.

| Old field | New field | Form |
|---|---|---|
| `phase` | `phase` | ref plan:phase; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| `revision` | `revision` | string |
| `base` | `base` | string |
| `kind` | `kind` | enum |

### project:assessment -> run:assessment

Pattern `current-status` -> lifecycle `current`. Sections: Evidence, Missing, Reason.

| Old field | New field | Form |
|---|---|---|
| `requirement` | `requirement` | string |
| `status` | `status` | enum |
| `level` | `level` | enum optional |
| `next` | `next` | enum |
| `confidence` | `confidence` | enum |
| `phase` | `phase` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `missing` | `missing` | string optional |

### project:release -> run:release

Pattern `current-status` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `state` | `state` | enum |
| `phase` | `phase` | string |
| `effort` | `effort` | ref plan:effort; str>ref |

### project:feedback -> plan:feedback

Pattern `observation` -> lifecycle `event`. Sections: Signal.

| Old field | New field | Form |
|---|---|---|
| `source` | `source` | string |
| `signal` | `signal` | string |
| `effort` | `effort` | ref plan:effort; str>ref |
| `phase` | `phase` | string optional |

### project:backlog-item -> plan:backlog-item

Pattern `current-status` -> lifecycle `current`.

| Old field | New field | Form |
|---|---|---|
| `effort` | `effort` | ref plan:effort; str>ref |
| `status` | `status` | enum |
| `source` | `source` | string optional |
| `phase` | `phase` | ref plan:phase optional; str>ref |

### project:oracle-amendment -> aff:oracle-amendment

Pattern `current-status` -> lifecycle `current`. Sections: Reason, Change.

| Old field | New field | Form |
|---|---|---|
| `acceptance` | `acceptance` | ref plan:acceptance; str>ref |
| `effort` | `effort` | ref plan:effort; str>ref |
| `phase` | `phase` | ref plan:phase; str>ref |
| `old_hashes` | `old_hashes` | string |
| `new_hashes` | `new_hashes` | string |
| `status` | `status` | enum |

### project:evidence-observation -> aff:evidence-observation

Pattern `observation` -> lifecycle `event`.

| Old field | New field | Form |
|---|---|---|
| `technique` | `technique` | string |
| `base_rev` | `base_rev` | string |
| `head_rev` | `head_rev` | string |
| `result` | `result` | string |
| `claim_ids` | `claim_ids` | list of string; str>list |
| `effort` | `effort` | ref plan:effort optional; str>ref |
| `replay` | `replay` | string optional |

## Judgment calls

- Scalar types come from record data. `duration_s` is `number` (1343 floats, 2 ints). `exit_code`, `ordinal`, `estimate_minutes`, `attempts` are `integer`. `blocking` is `boolean`.
- `check-run.failing_node_ids` holds a JSON array encoded as a string in 214 of 292 records, and plain comma-separated text in the rest. The migration must JSON-decode a value that starts with `[` and split on `,` otherwise.
- `plan:effort.merged_from` is a list of strings; 1 record already holds a list.
- `oracle-amendment.old_hashes` and `new_hashes` stay `string`: no value holds a comma and the contract does not call them comma-separated.
- `phase` fields on `integration-report`, `assessment`, `release`, `feedback` stay `string`: the old contract had no `payload_references` entry for them. They could become `ref plan:phase` later.
- `check-run.criterion_id`, `evidence-binding.observation_id`, `evidence-binding.claim_id`, `assessment.requirement` stay `string`: no `payload_references` entry.
- `design.decisions` is required (old contract), so the migration writes `[]` for an empty value.
- `execution-report.assignment` holds `rec-` ids in 3 orchestra records; the migration maps them to subjects.

## Contract disagreements (orchestra vs affidavit)

- `phase`: orchestra has optional `milestone` (ref `project:milestone`); affidavit lacks the field. Orchestra wins.
- `milestone` and `proof-packet` exist only in orchestra's contract.
- `evidence-observation` exists only in affidavit's contract. Taken from affidavit.
- All other 23 shared types are identical.

## Payload keys in records but not in any contract

These keys fail validation once the modules apply. The migration must drop or handle them.

- `assignment.subject` (3), `execution-report.subject` (3): duplicate of the envelope subject.
- `execution-report.effort` (11 records).
- `finding.severity` (3).
- `continuity-question.question` (1).
- `release.revision` (3).
