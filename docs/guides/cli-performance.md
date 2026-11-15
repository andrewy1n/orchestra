# CLI performance regression suite

Run commands from the repository root. Use the same Python version and machine for comparisons.

```sh
uv run python -m scripts.benchmark_cli run --output /tmp/cli-before.json
```

The runner creates local temporary stores with exactly 100, 1,000, and 6,000 records.
Each store has phases, requirements, tasks, dependencies, acceptances, and check history.
Each store includes fixed project policy in `orchestra.toml`.
Record data, schema snapshots, and project policy produce a fixture fingerprint.
The runner uses Canon storage APIs and excludes fixture setup from command timings.
It removes each temporary store when the run ends.
Parent store paths and Git environment overrides cannot redirect fixture setup or command execution.

Each case starts a fresh Python process from the current checkout.
Cases cover CLI help, record lookup, full listing, filtered listing, validation, handoff,
plan, status, verification, and task briefs.
Output checks verify record counts, record identity, or seeded view content.
A successful exit with missing output fails the case.

The default run takes three samples per case with a ten-second limit per sample.
There is no cache flush or separate warmup pass.
Processes start fresh, but operating system caches can stay warm across samples.
Reported wall time includes process launch, output capture, and controller wait overhead.
The wait controller polls process completion, which adds timing jitter to short commands.
Use repeated measurements and a quiet host when comparing small differences.

Run a smaller selection during development:

```sh
uv run python -m scripts.benchmark_cli run \
  --sizes 100 --repeat 1 --timeout 5 \
  --cases orchestra-help canon-get status \
  --output /tmp/cli-smoke.json
```

Use `--help` for arguments. Available case names are:

- `orchestra-help`
- `canon-help`
- `canon-get`
- `canon-list`
- `canon-list-filtered`
- `canon-validate`
- `handoff`
- `plan`
- `status`
- `verification`
- `brief`

The runner writes JSON after each case. Reports contain the source revision, dirty-tree state,
Python and platform details, initial host load, fixture fingerprint, command arguments,
individual sample times, output sizes, median, minimum, and maximum.
Failures include bounded output excerpts. A failed case stops its remaining repetitions.
Later cases still run. A timeout terminates the process group and kills surviving children.

Exit codes are:

- `0`: All measured cases pass their output checks.
- `1`: At least one case fails or times out. The JSON report remains available.
- `2`: Arguments, report input, or setup fail.

Compare saved reports:

```sh
uv run python -m scripts.benchmark_cli compare /tmp/cli-before.json /tmp/cli-after.json
```

Comparison requires the same case set, timeout, fixture version, fixture fingerprints,
and command arguments. Repetition counts can differ.
A positive percentage means the later report is slower.
Timing differences are reports only. They do not set a failure threshold.
Failed cases show their status without a timing percentage.
Check report environment details before attributing a difference to code.

To compare revisions, run this module in each checkout and keep both JSON reports.
Keep the fixture generator unchanged. A schema or fixture change can require a new baseline.
Save reports in a durable location when you need a baseline beyond the current session.

These fixtures provide a stable workload. They do not reproduce every live store shape.
Store history, phase distribution, record bodies, and host load can change observed performance.
Use a profile of the actual slow command to guide a later repair.
This suite changes no production behavior and adds no blocking CI timing gate.

Run the regression checks:

```sh
uv run pytest -q tests/test_cli_performance.py
```

Tests cover fixture validity, command output, report comparison, store isolation,
and process-group cleanup. They contain no command-speed assertions.
