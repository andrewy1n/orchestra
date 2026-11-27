from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from orchestra.canon.types import Record
from orchestra.composer.architecture_change import dependency_changes, proposal_for_phase
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex
from orchestra.conductor.verification.standing_constraints import proposed_constraint_outcome


def architecture_review(
    project_records: Sequence[Record], work: Path, phase: str, base: str, head: str
) -> str:
    proposal = proposal_for_phase(project_records, phase)
    if proposal is None:
        return ""
    dependencies = dependency_changes(project_records, work, base, head)
    lines = [
        "## Proposed architecture changes",
        "",
        f"Proposal {proposal.record['id']} at {proposal.record['revision']} ({proposal.status})",
        f"Baseline {dependencies.baseline}",
        f"Candidate {dependencies.candidate}",
        "",
        f"ADR {proposal.adr} affects {', '.join(proposal.affects)}.",
        proposal.rationale,
        f"ADR enforcement rules {', '.join(proposal.enforced_by) or 'none'}",
    ]
    evidence = EvidenceIndex(project_records)
    for change in proposal.constraints:
        lines.append(
            f"- {change.operation.capitalize()} constraint {change.subject} ({change.record['id']})"
        )
        if change.operation != "retire":
            status = proposed_constraint_outcome(
                evidence, change.record["id"], change.record["revision"], dependencies.candidate
            )
            targets = change.payload["targets"]
            target_names = (
                ", ".join(str(target) for target in targets) if isinstance(targets, list) else ""
            )
            lines.extend(
                (
                    f"  - {change.subject}: {status}. {change.payload['rule']}",
                    f"  - Area {change.payload['area']}",
                    f"  - Targets {target_names or 'none'}",
                    "  - Check command",
                    "",
                )
            )
            lines.extend(f"        {line}" for line in str(change.payload["check"]).splitlines())
            lines.append("")
        lines.append(f"  - {change.basis}")
    lines.extend(("", "## Observed component dependency changes", ""))
    if not dependencies.has_mappings:
        lines.append("No component module mappings declared.")
        return "\n".join(lines) + "\n"
    lines.extend(f"- Added: {source} → {target}" for source, target in dependencies.added)
    lines.extend(f"- Removed: {source} → {target}" for source, target in dependencies.removed)
    if not (dependencies.added or dependencies.removed):
        lines.append("No component dependency changes observed.")
    if dependencies.unmapped:
        lines.append("Unmapped first-party modules " + ", ".join(dependencies.unmapped))
    return "\n".join(lines) + "\n"
