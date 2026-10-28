"""Session metrics behind ``orchestra sessions``."""

from __future__ import annotations

from pathlib import Path


def report(root: str | Path | None = None, *, records: bool = False) -> int:
    """Print one JSON summary per transcript under ``root``."""
    from orchestra.sessions.session_report import main

    argv: list[str] = []
    if records:
        argv.append("--records")
    if root is not None:
        argv.append(str(root))
    return main(argv)


def aggregate(report_path: str | Path | None = None) -> int:
    """Print one aggregate document for a report JSONL file (or stdin)."""
    from orchestra.sessions.session_aggregate import main

    # session_aggregate.main() expects a script-name slot at argv[0].
    argv = ["orchestra sessions aggregate"]
    if report_path is not None and str(report_path) != "-":
        argv.append(str(report_path))
    return main(argv)
