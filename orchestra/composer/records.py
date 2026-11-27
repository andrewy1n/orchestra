from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_blank_text, optional_text_list, required_text
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import latest_record

IDEA = "composer:idea"
AREA = "composer:area"
PLACEMENT = "composer:placement"
PRODUCT = "composer:product"
PRODUCT_ITEM = "composer:product-item"
PRODUCT_SUBJECT = "product"
COMPONENT = "composer:component"
INTERFACE = "composer:interface"
ARCHITECTURE_DECISION = "composer:architecture-decision"

_ITEM_STATUSES = ("current", "planned")
_DECISION_STATUSES = ("accepted", "proposed")
_DEAD_STATES = ("superseded", "retracted")


@dataclass(frozen=True)
class Idea:
    subject: str
    status: str
    area: str
    effort: str
    phase: str
    source: str
    text: str
    record: Record


@dataclass(frozen=True)
class Area:
    subject: str
    title: str
    scope: str


@dataclass(frozen=True)
class Placement:
    effort: str
    area: str


@dataclass(frozen=True)
class ComposerScanFinding:
    record_id: str
    record_type: str
    field: str
    message: str


@dataclass(frozen=True)
class Product:
    purpose: str
    audience: str
    record: Record


@dataclass(frozen=True)
class ProductItem:
    title: str
    description: str
    status: str
    record: Record
    area: str | None = None


@dataclass(frozen=True)
class Component:
    name: str
    area: str
    responsibility: str
    record: Record
    module_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Interface:
    name: str
    provides: str
    connects: tuple[str, ...]
    record: Record


@dataclass(frozen=True)
class ArchitectureDecision:
    title: str
    rationale: str
    status: str
    affects: tuple[str, ...]
    enforced_by: tuple[str, ...]
    record: Record


def _idea_text(record: Record) -> str:
    for line in (record.get("body") or "").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return record["subject"]


def _section(body: str, name: str) -> str:
    lines: list[str] = []
    inside = False
    for line in body.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower() == name
        elif inside:
            lines.append(line)
    return "\n".join(lines).strip()


def _scope(body: str) -> str:
    return _section(body, "scope")


def _required_section(record: Record, name: str) -> str:
    text = _section(record.get("body") or "", name.lower())
    if not text:
        raise RecordShapeError(record["id"], "body", f"needs a non-empty ## {name} section")
    return text


def _required_list(record: Record, payload: JsonObject, field: str) -> tuple[str, ...]:
    if field not in payload:
        raise RecordShapeError(record["id"], field, "is required")
    values = optional_text_list(record, payload, field)
    if not values:
        raise RecordShapeError(record["id"], field, "must not be empty")
    return values


def read_idea(record: Record) -> Idea:
    payload = record_payload(record)
    return Idea(
        subject=record["subject"],
        status=required_text(record, payload, "status"),
        area=optional_blank_text(record, payload, "area") or "",
        effort=optional_blank_text(record, payload, "effort") or "",
        phase=optional_blank_text(record, payload, "phase") or "",
        source=optional_blank_text(record, payload, "source") or "",
        text=_idea_text(record),
        record=record,
    )


def read_area(record: Record) -> Area:
    payload = record_payload(record)
    return Area(
        subject=record["subject"],
        title=optional_blank_text(record, payload, "title") or record["subject"],
        scope=_scope(record.get("body") or ""),
    )


def read_placement(record: Record) -> Placement:
    payload = record_payload(record)
    return Placement(effort=record["subject"], area=required_text(record, payload, "area"))


def read_product(record: Record) -> Product:
    payload = record_payload(record)
    return Product(
        purpose=required_text(record, payload, "purpose"),
        audience=required_text(record, payload, "audience"),
        record=record,
    )


def read_product_item(record: Record) -> ProductItem:
    payload = record_payload(record)
    status = required_text(record, payload, "status")
    if status not in _ITEM_STATUSES:
        raise RecordShapeError(record["id"], "status", "must be current or planned")
    return ProductItem(
        title=required_text(record, payload, "title"),
        description=required_text(record, payload, "description"),
        status=status,
        record=record,
        area=optional_blank_text(record, payload, "area"),
    )


def read_component(record: Record) -> Component:
    payload = record_payload(record)
    return Component(
        name=record["subject"],
        area=required_text(record, payload, "area"),
        responsibility=_required_section(record, "Responsibility"),
        record=record,
        module_prefixes=optional_text_list(record, payload, "module_prefixes"),
    )


def read_interface(record: Record) -> Interface:
    payload = record_payload(record)
    return Interface(
        name=record["subject"],
        provides=_required_section(record, "Provides"),
        connects=_required_list(record, payload, "connects"),
        record=record,
    )


def read_architecture_decision(record: Record) -> ArchitectureDecision:
    payload = record_payload(record)
    status = required_text(record, payload, "status")
    if status not in _DECISION_STATUSES:
        raise RecordShapeError(record["id"], "status", "must be accepted or proposed")
    return ArchitectureDecision(
        title=record["subject"],
        rationale=_required_section(record, "Rationale"),
        status=status,
        affects=_required_list(record, payload, "affects"),
        enforced_by=optional_text_list(record, payload, "enforced_by"),
        record=record,
    )


def _live(records: Sequence[Record], record_type: str) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == record_type and record["lifecycle_state"] not in _DEAD_STATES
    ]


def current_area(records: Sequence[Record], subject: str) -> Area | None:
    record = latest_record(r for r in _live(records, AREA) if r["subject"] == subject)
    return read_area(record) if record is not None else None


def current_product(records: Sequence[Record]) -> Product | None:
    statements = _live(records, PRODUCT)
    for record in statements:
        if record["subject"] != PRODUCT_SUBJECT:
            raise RecordShapeError(
                record["id"], "subject", f"a product statement must use subject {PRODUCT_SUBJECT}"
            )
    if len(statements) > 1:
        raise RecordShapeError(
            statements[-1]["id"],
            "subject",
            f"{len(statements)} live product statements exist; keep one",
        )
    return read_product(statements[0]) if statements else None


def current_product_items(records: Sequence[Record]) -> list[ProductItem]:
    items = [read_product_item(record) for record in _live(records, PRODUCT_ITEM)]
    return sorted(items, key=lambda item: (item.record["subject"], item.record["id"]))


def current_placements(records: Sequence[Record]) -> dict[str, str]:
    by_effort: dict[str, list[Record]] = {}
    for record in _live(records, PLACEMENT):
        by_effort.setdefault(record["subject"], []).append(record)
    placements: dict[str, str] = {}
    for efforts in by_effort.values():
        latest = latest_record(efforts)
        if latest is not None:
            placement = read_placement(latest)
            placements[placement.effort] = placement.area
    return placements


def open_ideas(records: Sequence[Record]) -> list[Idea]:
    ideas = [
        read_idea(record) for record in records if record.get("lifecycle_state") not in _DEAD_STATES
    ]
    return sorted(
        (idea for idea in ideas if idea.status == "open"),
        key=lambda idea: (idea.subject, idea.record["id"]),
    )


def home_area(idea: Idea, placements: Mapping[str, str]) -> str:
    if idea.status == "promoted":
        placed = placements.get(idea.effort)
        if placed:
            return placed
    return idea.area


def scan_composer_records(records: Sequence[Record]) -> list[ComposerScanFinding]:
    readers = {
        IDEA: read_idea,
        AREA: read_area,
        PLACEMENT: read_placement,
        PRODUCT: read_product,
        PRODUCT_ITEM: read_product_item,
    }
    findings: list[ComposerScanFinding] = []
    for record in records:
        reader = readers.get(record["record_type"])
        if reader is None or record["lifecycle_state"] in _DEAD_STATES:
            continue
        try:
            reader(record)
        except RecordShapeError as error:
            findings.append(
                ComposerScanFinding(
                    error.record_id, record["record_type"], error.field, error.message
                )
            )
    try:
        current_product(records)
    except RecordShapeError as error:
        findings.append(ComposerScanFinding(error.record_id, PRODUCT, error.field, error.message))
    return findings
