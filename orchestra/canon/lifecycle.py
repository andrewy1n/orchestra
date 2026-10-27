"""The five built-in lifecycles."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lifecycle:
    name: str
    initial: str
    transitions: dict[str, tuple[str, ...]]

    @property
    def states(self) -> tuple[str, ...]:
        seen = [self.initial]
        for src, dests in self.transitions.items():
            for state in (src, *dests):
                if state not in seen:
                    seen.append(state)
        return tuple(seen)

    def allows(self, src: str, dest: str) -> bool:
        return dest in self.transitions.get(src, ())

    @property
    def appends_only(self) -> bool:
        return self.name == "event"

    @property
    def supersedable(self) -> bool:
        return "superseded" in self.states


LIFECYCLES: dict[str, Lifecycle] = {
    "current": Lifecycle("current", "active", {"active": ("superseded",)}),
    "staged": Lifecycle(
        "staged",
        "planned",
        {
            "planned": ("in_progress", "withdrawn", "superseded"),
            "in_progress": ("done", "withdrawn", "superseded"),
            "done": ("superseded",),
        },
    ),
    "event": Lifecycle("event", "recorded", {}),
    "question": Lifecycle(
        "question",
        "open",
        {
            "open": ("answered", "deferred", "closed"),
            "deferred": ("open", "closed"),
        },
    ),
    "claim": Lifecycle(
        "claim",
        "asserted",
        {
            "asserted": ("supported", "disputed", "refuted", "retracted"),
            "supported": ("disputed", "refuted", "retracted"),
            "disputed": ("supported", "refuted", "retracted"),
        },
    ),
}


def terminal_success_state(lifecycle: Lifecycle) -> str | None:
    """The state meaning "done, successfully": the deepest dead end that is not `superseded`."""
    transitions = lifecycle.transitions

    def progress(state: str) -> list[str]:
        return [dest for dest in transitions.get(state, ()) if dest != "superseded"]

    candidates = [s for s in lifecycle.states if s != "superseded" and not progress(s)]
    distances = {lifecycle.initial: 0}
    frontier = [lifecycle.initial]
    while frontier:
        following: list[str] = []
        for state in frontier:
            for dest in transitions.get(state, ()):
                if dest not in distances:
                    distances[dest] = distances[state] + 1
                    following.append(dest)
        frontier = following
    reachable = [s for s in candidates if s in distances and s != lifecycle.initial]
    if not reachable:
        return None
    farthest = max(distances[s] for s in reachable)
    return sorted(s for s in reachable if distances[s] == farthest)[0]
