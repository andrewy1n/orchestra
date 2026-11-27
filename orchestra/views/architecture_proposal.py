from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from importlib.util import resolve_name
from pathlib import Path, PurePosixPath

from orchestra.canon.types import Record
from orchestra.composer.architecture_proposal import proposal_for_phase
from orchestra.composer.records import COMPONENT, read_component
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex
from orchestra.conductor.verification.standing_constraints import proposed_constraint_outcome
from orchestra.tools import Git

Edge = tuple[str, str]


def proposed_constraint(records: Sequence[Record], phase: str, change_id: str) -> Record | None:
    proposal = proposal_for_phase(records, phase)
    if proposal is None or proposal.status != "pending":
        return None
    return next(
        (
            change.record
            for change in proposal.constraints
            if change.record["id"] == change_id and change.operation != "retire"
        ),
        None,
    )


def _prefixes(records: Sequence[Record]) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for record in records:
        if record["record_type"] != COMPONENT or record["lifecycle_state"] != "active":
            continue
        component = read_component(record)
        for prefix in component.module_prefixes:
            if prefix in prefixes and prefixes[prefix] != record["subject"]:
                raise ValueError(f"Multiple components declare module prefix {prefix!r}.")
            prefixes[prefix] = record["subject"]
    return prefixes


def _component(module: str, prefixes: dict[str, str]) -> str | None:
    while module:
        if module in prefixes:
            return prefixes[module]
        module = module.rpartition(".")[0]
    return None


def _imports(tree: ast.Module, package: str) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                try:
                    module = resolve_name("." * node.level + module, package)
                except ImportError:
                    yield "." * node.level + module
                    continue
            if module:
                yield from (
                    module if alias.name == "*" else f"{module}.{alias.name}"
                    for alias in node.names
                )


def _edges(git: Git, revision: str, prefixes: dict[str, str]) -> set[Edge]:
    edges: set[Edge] = set()
    listing = git.text("ls-tree", "-r", "-z", revision)
    for entry in listing.split("\0"):
        metadata, _, name = entry.partition("\t")
        if not name.endswith(".py") or not metadata.startswith(("100644 blob ", "100755 blob ")):
            continue
        path = PurePosixPath(name)
        parts = path.with_suffix("").parts
        if parts[0] == "src":
            parts = parts[1:]
        package = ".".join(parts[:-1])
        module = package if path.stem == "__init__" else ".".join(parts)
        source = _component(module, prefixes)
        content = git.show_bytes(revision, name)
        if content is None:
            raise RuntimeError(f"Cannot read {name} at {revision}.")
        try:
            tree = ast.parse(content, filename=name)
        except SyntaxError:
            edges.add((source or f"unresolved module {module}", f"unresolved imports in {name}"))
            continue
        for target in _imports(tree, package):
            owner = _component(target, prefixes)
            if source != owner or source is None:
                edges.add(
                    (
                        source or f"unresolved module {module}",
                        owner or f"unresolved module {target}",
                    )
                )
    return edges


def architecture_review(
    project_records: Sequence[Record], work: Path, phase: str, base: str, head: str
) -> str:
    proposal = proposal_for_phase(project_records, phase)
    if proposal is None:
        return ""
    git = Git(work)
    baseline = git.resolve(base)
    candidate = git.resolve(head)
    if baseline is None or candidate is None:
        raise ValueError("Architecture review requires a resolvable base and candidate commit.")
    lines = [
        "## Proposed architecture changes",
        "",
        f"Proposal {proposal.record['id']} at {proposal.record['revision']} ({proposal.status})",
        f"Baseline {baseline}",
        f"Candidate {candidate}",
        "",
        f"ADR {proposal.adr} affects {', '.join(proposal.affects)}.",
        proposal.rationale,
    ]
    evidence = EvidenceIndex(project_records)
    for change in proposal.constraints:
        lines.append(
            f"- {change.operation.capitalize()} constraint {change.subject} ({change.record['id']})"
        )
        if change.operation != "retire":
            status = proposed_constraint_outcome(
                evidence, change.record["id"], change.record["revision"], candidate
            )
            lines.append(f"  - {change.subject}: {status}. {change.payload['rule']}")
        lines.append(f"  - {change.basis}")
    lines.extend(("", "## Observed component dependency changes", ""))
    prefixes = _prefixes(project_records)
    if not prefixes:
        lines.append("No component module mappings declared.")
    before = _edges(git, baseline, prefixes)
    after = _edges(git, candidate, prefixes)
    lines.extend(f"- Added: {a} → {b}" for a, b in sorted(after - before))
    lines.extend(f"- Removed: {a} → {b}" for a, b in sorted(before - after))
    if before == after:
        lines.append("No dependency changes observed.")
    return "\n".join(lines) + "\n"
