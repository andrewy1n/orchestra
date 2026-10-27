# canon schema modules

Specification of the canon record store.
This format replaces the adaptive contract layer: traits, patterns, the
catalog, `resolve`, `lock`, `source_lock`, backends, `project-design.json`,
`resolved-contract.json`, and `meta.json`.

## Goals

- Each tool owns its record types in one schema module.
- No tool copies another tool's types.
- A project composes modules by listing them. Nothing merges or resolves them.
- The store validates every write, references included.

## Non-goals

- Agent-designed schemas for each project.
- A declarative view language. Tools render views in code.
- Capture and read policies. Skills carry that guidance.
- Bundles. `apply` batches replace them.
- Reading the old format. The cutover is a one-shot migration.

## Lifecycles

canon has five built-in lifecycles. A type picks one. Lifecycles do not
compose.

| Lifecycle | Initial | Transitions | Store mechanics |
|---|---|---|---|
| `current` | `active` | `active` → `superseded` | At most one `active` record per type and subject. `supersede` writes a successor with a new id and moves the old record to `superseded`. |
| `staged` | `planned` | `planned` → `in_progress`, `withdrawn`, `superseded`; `in_progress` → `done`, `withdrawn`, `superseded`; `done` → `superseded` | Built-in `depends_on` field. canon derives `ready` and `wave`. |
| `event` | `recorded` | none | Append only. `correct` writes a successor that names the original in `relationships.corrects`. canon derives `corrected` on the original. |
| `question` | `open` | `open` → `answered`, `deferred`, `closed`; `deferred` → `open`, `closed` | — |
| `claim` | `asserted` | `asserted` → `supported`, `disputed`, `refuted`, `retracted`; `supported` → `disputed`, `refuted`, `retracted`; `disputed` → `supported`, `refuted`, `retracted` | — |

Event types reuse subjects. For example, one task has several
execution-reports with the task slug as subject. Only `current` enforces one
active record per subject.

## Module file

A module is one JSON file inside the owning tool's package.

```json
{
  "namespace": "run",
  "version": "0.1.0",
  "types": {
    "assignment": {
      "purpose": "What the orchestrator handed an executor for a work-item",
      "lifecycle": "event",
      "fields": {
        "work_item": {"ref": "score:work-item"},
        "executor":  {"enum": ["inline", "subagent"]},
        "effort":    {"ref": "score:effort"}
      },
      "sections": ["Orientation"]
    }
  },
  "migrations": []
}
```

A type has four keys:

- `purpose`: one line for agents and for `--help`. Required.
- `lifecycle`: one of the five built-ins. Required.
- `fields`: the payload fields. Required; may be empty.
- `sections`: the Markdown `## ` headings the body must contain. Optional.

A module rejects unknown keys. A module may reference types in other
namespaces.

## Fields

A field is required unless it sets `"optional": true`. A payload key that the
type does not declare fails validation.

| Form | Value |
|---|---|
| `{"type": "string"}` | string |
| `{"type": "integer"}` | JSON integer |
| `{"type": "number"}` | JSON integer or float |
| `{"type": "boolean"}` | JSON boolean |
| `{"enum": [...]}` | one listed string |
| `{"ref": "<ns>:<type>"}` | subject of a record of that type |
| `{"ref": ["<ns>:<a>", "<ns>:<b>"]}` | subject of a record of any listed type |
| `{"ref": ..., "pin": true}` | id of one exact record |
| `{"list": <form>}` | JSON array of that form |

A required string field may hold `""`. An enum field may hold `""` only when
it is optional.

### References

A subject reference resolves to the latest record of the target type with
that subject, by `recorded_at`. A pinned reference resolves to the record with
that id.

canon checks every reference on every write: `create`, `update`,
`supersede`, `correct`, and each `apply` operation. The write fails when the
target type is not installed, or when no record matches. An empty string or
an empty list is not checked.

`canon validate` checks every reference in the store.

### Built-in fields

- Every `staged` type has `depends_on`: `{"list": {"ref": <same type>},
  "optional": true}`. It holds subjects.
- `relationships` holds only `supersedes` and `corrects`. Both hold record
  ids. canon writes them. A caller never sets them.

Every other link is a declared field. Examples:

- check-run `informed_by`:
  `{"list": {"ref": ["score:acceptance", "conductor:execution-report"], "pin": true}, "optional": true}`
- finding `contradicted_by`:
  `{"list": {"ref": "tuner:finding", "pin": true}, "optional": true}`

## Record file

The file format stays: a JSON front-matter block between `---` lines, then a
Markdown body. The path is
`.canon/records/<namespace>__<type>/<id>.md`.

Envelope keys:

| Key | Rule |
|---|---|
| `id` | `rec-<uuid4>`. |
| `record_type` | `<namespace>:<type>`. |
| `subject` | Non-empty slug. |
| `lifecycle_state` | A state of the type's lifecycle. |
| `payload` | Object that matches `fields`. |
| `relationships` | Object with optional `supersedes` and `corrects` lists. |
| `recorded_at` | ISO 8601 UTC. |
| `revision` | `sha256:` over the canonical record, as computed today. |
| `time` | Optional. Kept as written. Not validated. |
| `provenance` | Optional. Kept as written. Not validated. |

These keys go: `base_kind`, `identity`, `stewardship`, `epistemic_status`.

## Project config

`.canon/config.json` marks a store and lists its namespaces. It replaces
`meta.json`.

```json
{
  "format": "canon/1",
  "schemas": {"plan": "0.1.0", "run": "0.1.0", "aff": "0.1.0"},
  "settings": {
    "conductor": {"phase_gate": {"suite": {"mode": "none", "command": "", "gate": "required"}}}
  }
}
```

`settings` holds per-tool configuration. canon does not read it. Each tool
reads and writes its own key.

## Discovery and snapshots

A tool registers its module in the `canon.schemas` entry point group. The
entry point name is the namespace. The value names an importable package that
holds `<namespace>.json`, for example `run = "orchestra.schemas"`. The value
cannot hold a path, because packaging accepts only object references there.

`canon schemas sync`:

1. Finds every installed module through the entry points.
2. Copies each module named in `config.json` to
   `.canon/schemas/<namespace>.json`.
3. Runs any migrations between the old and new snapshot versions.
4. Writes the new versions into `config.json`.
5. Runs `validate`.

`canon schemas add <namespace>` adds an installed module to `config.json` and
syncs it. `canon init --schemas score,conductor,tuner` creates the store with those
modules.

canon validates against the snapshots only, never against installed packages.
Two clones with different tool versions validate the same way. The store stays
readable without the tools installed.

## Versioning

- Additive change: a new type, a new optional field, or a new enum value.
  Bump the minor version. Old records stay valid.
- Breaking change: a rename, a removed field, or a new required field. Bump
  the major version and add a migration.

```json
"migrations": [
  {"from": "1", "to": "2",
   "rename_type": {"conductor:report": "conductor:execution-report"},
   "rename_field": {"conductor:execution-report": {"status": "result"}},
   "map_enum": {"conductor:execution-report.result": {"ok": "done"}}}
]
```

`from` and `to` are major versions. Migrations are declarative only. A change
they cannot express needs a script in the tool.

## CLI

`canon` keeps: `init`, `create`, `update`, `supersede`, `correct`, `apply`,
`get`, `list`, `validate`, `schemas sync`, `schemas add`, `schemas show`.

`canon validate --format json` prints the error list. Orchestra's Stop hook
compares it with a saved baseline and blocks only on new errors.

`canon migrate-legacy` is a one-shot command. It converts a store in the old
format. See `docs/history/canon-migration-plan.md`.

canon drops: `resolve`, `lock`, `capture`, `contradict`, `handoff`, `view`,
`watch`, `brief`, `hook-start`, `hook-stop`.

The library keeps `canon.project.open_store`, `Project.get`, `Project.list`,
`Project.create`, `Project.apply`, the error types, the query helpers, and the
derive helpers (`ready`, `wave`, `corrected`, inverse links).

## Namespaces

| Namespace | Owner | Types |
|---|---|---|
| `plan` | orchestra (planner later) | effort, position, milestone, phase, specification, design, decision, constraint, work-item, acceptance, backlog-item, feedback, continuity-question |
| `run` | orchestra | assignment, assignment-amendment, execution-report, integration-report, assessment, release, proof-packet, failed-attempt |
| `aff` | tuner | check-run, evidence-observation, evidence-binding, oracle-amendment, investigation-observation, finding |

### Effort

`score:effort` replaces `active-goal`. The goal record already is the effort:
its subject is the effort slug, and it carries `goal`, `kind`, `status`, and
`merged_from`. `score:effort` keeps those fields and drops `scope`. Every
`effort` field is `{"ref": "score:effort"}`.

`score:position` replaces `current-position`.

## Transition owners

Write ownership follows transitions, not namespaces. A tool may move a record
in another tool's namespace when this table says so.

| Record | Planner | Orchestra |
|---|---|---|
| `score:phase` | create; `planned` → `in_progress`; `withdrawn`; `superseded` | `in_progress` → `done` at Landing |
| `score:work-item` | create; `withdrawn`; `superseded` | `planned` → `in_progress`; `in_progress` → `done` |
| `conductor:assessment` | reads it | writes it |

Orchestra moves a work-item to `done`. Only orchestra holds the evidence: the
execution-report, the check-runs, and the assessment. An assessment that
routes to `specify`, `design` or `plan` is the planner's input, like
`score:feedback`.

canon does not check the caller.

## Open questions

1. Name the orchestra step that moves a phase to `done`. No skill names it
   today, yet 75 of 80 phases in orchestra's store are `done`.
