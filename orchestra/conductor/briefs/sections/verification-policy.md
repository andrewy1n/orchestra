# Verification method and oracle policy

Choose `method` separately from `oracle_policy`. Record both choices during planning.

| Method | Oracle policy | Evidence needed to close |
|---|---|---|
| `tdd` | `none` | Runner-produced red before runner-produced green |
| `check` | `none` | Passing runner check |
| `tdd` | `frozen` | Assertion-level red, green, and matching frozen hashes |
| `check` | `frozen` | Green and matching frozen hashes; no red required |
| `manual` | `none` | Human sign-off |

`manual` with `frozen` is invalid. An approved oracle amendment can authorize hash changes.
Manifest claims also retain their separate verdict and recheck gates.

## Select and record

Select `tdd` when an assertion failure can demonstrate missing behavior or a bug.
Select `check` for routine verification such as building a wheel, running an
installer smoke check, checking documentation, or running the final suite.
Select `frozen` when independent tests against a stable interface justify the authoring cost.
Bug reproductions and compatibility contracts are good candidates.
Do not select frozen oracles for every deliver or repair task automatically.

A phase can set `oracle_policy` to `none` or `frozen`. The default is `none`.
An acceptance can override that default. Stamp the resolved `oracle_policy` on every new acceptance.
A phase default is a planning convenience; explicit acceptance policy fixes the choice for execution.
Existing acceptance freeze metadata still selects `frozen` when explicit policy is absent.
Never remove existing hashes or set `none` to bypass an existing freeze.
Reject partial freeze metadata, `none` with freeze metadata, and `frozen` without complete metadata.

An ordinary acceptance has `oracle_policy: none` and omits `test_ids` and `oracle_hashes`.
Its tests need not exist during planning. An executor writes unfrozen TDD tests during execution,
records red through `orchestra check`, implements the behavior, and records green.
An import or collection failure does not prove that an assertion detects incorrect behavior.
For a new API, create the minimum importable interface and confirm a behavior failure before implementing that behavior.

## Before TDD implementation

For each unfrozen TDD acceptance, prepare the test first. Have the parent run
`orchestra check` in the task worktree and confirm that the expected assertion
fails. Use evidence of that failure to release implementation. For a frozen
acceptance, confirm the recorded assertion-level red and the frozen hashes.
If the test already passes, check if the approved behavior already exists or
if the test misses the required case. Fix invalid commands and test setup first.
Keep the task at this step until the red proof or a permitted correction exists.

## Selected frozen acceptances

Skip oracle authoring when no acceptance selects `frozen`.
Otherwise use one independent oracle-author for only the selected frozen acceptances.
The author receives requirement text and the method, not implementation hints.
For frozen `tdd`, require assertion-level red before freezing.
For frozen `check`, tests can pass when authored; red is not required.
Create the acceptance with its policy, test ids, and hashes together.
Do not silently change selected policy when authoring cannot meet its contract.

## Changes during execution

The executor reports the proposed change and its evidence to the parent.
Require explicit parent approval before changing an acceptance. The parent
remains the only store writer. At `auto-plan` and `auto-phases`, the
parent can apply either correction to an unfrozen automated acceptance without
a new user decision:

- Repair the command when both versions select the same cases and assertions.
  Compare the test selectors and the relevant test changes. Preserve the method.
- Change `tdd` to `check` for documentation, packaging, or final verification
  when a passing result proves the same requirement. Keep the command and tests.
  Missing red evidence after implementing new behavior does not justify a switch.

Use `orchestra workflow amend-check <acceptance-id> --expected-revision <revision>`
with `--equivalent-command '<command>'` or `--routine-check <category>`.
Set `--basis` to the reason and the evidence. The command records an assignment
amendment. Refresh the task-plan review with `task-plan-policy` and cite the
amendment as its basis. Require a fresh passing check on the final revision.
At `gated`, ask before changing the acceptance. Ask for any change to required
behavior, test coverage, or proof outside these corrections.

Frozen file changes use the existing oracle amendment approval path.
Every frozen hash change requires a parent-approved `tuner:oracle-amendment` record, including changes to manifest claims.
The parent creates or supersedes that record with the acceptance subject, effort, phase, old hashes, new hashes, and approval reason.
Close-batch accepts approved `tuner:oracle-amendment` records whose new hashes match the green tree.
For manifest claims, the parent also uses the signed manifest and verdict path.
Unfrozen tests can change during implementation, but the declared TDD red-first contract still applies.
