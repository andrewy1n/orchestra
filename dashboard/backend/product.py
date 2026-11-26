"""The product statement with its capabilities and goals."""

from __future__ import annotations

from dataclasses import dataclass, field

from dashboard.backend.records import list_records, live_records
from orchestra.canon.project import Project
from orchestra.composer.records import (
    PRODUCT,
    PRODUCT_ITEM,
    ProductItem,
    current_product,
    current_product_items,
)


@dataclass(frozen=True)
class ProductStatement:
    purpose: str
    audience: str


@dataclass(frozen=True)
class ProductEntry:
    subject: str
    title: str
    description: str
    status: str


@dataclass(frozen=True)
class ProductOverview:
    statement: ProductStatement | None = None
    capabilities: list[ProductEntry] = field(default_factory=list)
    goals: list[ProductEntry] = field(default_factory=list)


def _entry(item: ProductItem) -> ProductEntry:
    return ProductEntry(
        subject=item.record["subject"],
        title=item.title,
        description=item.description,
        status=item.status,
    )


def load_product(target: Project) -> ProductOverview:
    statement = current_product(live_records(list_records(target, PRODUCT)))
    items = current_product_items(live_records(list_records(target, PRODUCT_ITEM)))
    return ProductOverview(
        statement=(
            ProductStatement(purpose=statement.purpose, audience=statement.audience)
            if statement
            else None
        ),
        capabilities=[_entry(item) for item in items if item.status == "current"],
        goals=[_entry(item) for item in items if item.status == "planned"],
    )
