# Canon SQLite cutover evidence

The cutover retained the pre-switch export outside the repository at
`~/.canon/orchestra/backups/pre-cutover.jsonl` (27 MB). The baseline count
snapshot is `~/.canon/orchestra/backups/pre-cutover-counts.json`. Neither file
is tracked by Git.

## Source verification

The source snapshot was checked with:

```text
python scripts/verify_import.py /tmp/cutover-live-source-store
```

The passing check recorded at phase commit
`7e981910a99600112c4838708e919f131ae151b2` reported:

```text
8770 retained history revisions checked
9983 records, 0 mismatches
```

## Post-switch database

The pre-switch baseline contained 9,983 records across 28 record types. The
live SQLite store was checked with the per-type count comparison against
`pre-cutover-counts.json`: 10,197 current records across 28 types, baseline
9,983 across 28 types, and every baseline type count was met.

## Preservation of record IDs and revisions

The export and the live store were compared by record ID, op, and revision
hash. Run the check on a read-only copy of the live database:

```text
mkdir -p /tmp/cutover-live
python -c "import sqlite3, pathlib as p; s = sqlite3.connect('file:' + str(p.Path.home() / '.canon/orchestra/canon.db') + '?mode=ro', uri=True); s.backup(sqlite3.connect('/tmp/cutover-live/canon.db'))"
python scripts/verify_preservation.py \
  ~/.canon/orchestra/backups/pre-cutover.jsonl /tmp/cutover-live
```

The check fails if any of these is false:

- Every record ID in the export is a current record in the live store.
- Every export op is in the live op chain, byte-equal.
- Every revision in the export, including retained history, hashes to its
  `revision` value and is in the live store unchanged, as a current record or
  as a history snapshot.

The check passed with `scripts/verify_preservation.py` as committed in `b26dfd07a`, against the export with SHA-256
`abbb83550c93a4b62aac9288a2b9d5d5f3d680b6ed82f450246d68254f61507a`:

```text
ops: 11421
revisions: 20191
records: 9983
live records: 10291
live records not in export: 308
export final revision still current: 9953
0 mismatches
```

The live store gains records after the cutover, so its count is higher than the
10,197 recorded below. 30 baseline records have a newer revision since the
cutover. The check finds their baseline revisions in history.

`canon validate` returned:

```json
{
  "status": "valid",
  "errors": [],
  "records": 10197
}
```

## Pushed-branch CI

The full CI workflow passed for `phase/cutover` at commit
`8ca55b34f5e8848333155731785f8553ce962482`. All jobs passed, including
`test-canon`, `test-tuner`, `test-orchestra`, `types`, `checks`, `wheel`,
`e2e`, and `web`.

[GitHub Actions run 41186899241](https://github.com/andrewy1n/orchestra/actions/runs/41186899241)

The tuner-verdict workflow also passed at that commit:

[GitHub Actions run 41186899238](https://github.com/andrewy1n/orchestra/actions/runs/41186899238)
