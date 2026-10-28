"""API routes shared by the stdlib server and the FastAPI app."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    """One dashboard API route."""

    method: str
    path: str
    reader_method: str
    query_keys: tuple[str, ...]


ROUTES = (
    Route("GET", "/api/token", "token", ()),
    Route("GET", "/api/snapshot", "snapshot", ()),
    Route("GET", "/api/phase", "phase", ("effort", "phase")),
    Route("GET", "/api/task", "task", ("id",)),
    Route("GET", "/api/journal", "journal", ("effort",)),
    Route("GET", "/api/record", "record", ("id",)),
    Route("GET", "/api/requirement", "requirement", ("effort", "phase", "id")),
    Route("GET", "/api/needs", "needs", ("effort", "id")),
    Route("GET", "/api/backlog", "backlog", ("effort", "id")),
    Route("POST", "/api/needs", "write_needs", ()),
    Route("POST", "/api/backlog", "write_backlog", ()),
)
