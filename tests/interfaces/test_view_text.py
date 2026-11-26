"""Pin the text printed by `orchestra handoff` and `orchestra view` for fixed records."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from interfaces.interfaces_support import build_world, invoke, seed_view_records

BANNER = "> Derived view — not authoritative. Edit underlying records, not this file.\n"
ID = "_(id: rec-<id>)_"
WORK_A = (
    "- **a**: Task a; p1; deliver; alpha; assignee: inline; write root: <root>/.worktrees/p1--a"
)
PROGRESS = (
    "### Progress\n- 0/2 done (planned: 1, in_progress: 1, done: 0)\n- in progress: a\n\n"
    "### Requirements\n- **R1**: unverified\n\n"
    "### Stage\n- spec (approval review is missing)\n"
)

HANDOFF = f"""# Project Handoff

{BANNER}
## alpha (live)

### Goal
- **alpha**: Goal of alpha; deliver {ID}

### Position
- **alpha**: midway; effort {ID}

### In Progress
{WORK_A} {ID}

## which-store

### Blocking Question
- **which-store**: True; alpha {ID}

"""

PLAN = f"""# Project Plan

{BANNER}
## p1

### Phase
- **p1**: Phase one; 1; alpha {ID}

### Work
{WORK_A}; executor: inline {ID}
- **b**: Task b; p1; deliver; alpha; executor: inline {ID}

### Acceptance
- **a**: R1; check; alpha; true {ID}

{PROGRESS}
"""

STATUS = f"""# Project Status

{BANNER}
## p1

### Work
- **a**: Task a; p1; deliver; alpha; state: in_progress; ready: True; wave: 1; assignee: inline; write root: <root>/.worktrees/p1--a; criteria: 0 pass / 0 fail {ID}
- **b**: Task b; p1; deliver; alpha; state: planned; ready: False; wave: 2; criteria: 0 pass / 0 fail {ID}

{PROGRESS}
"""

VERIFICATION = f"""# Project Verification

{BANNER}
## a

### Acceptance
- **a**: R1; check; alpha; true {ID}

## Phase p1

{PROGRESS}
"""

ROADMAP = f"""# Project Roadmap

{BANNER}
## Product

_No product statement._

## Capabilities

_No capabilities._

## Goals

_No goals._

## dashboard

### Area
- **dashboard**: Dashboard {ID}

### Idea
- **dark-mode**: open {ID}
- **shipped-thing**: promoted; alpha {ID}

## untriaged

### Idea
- **loose-end**: open {ID}

"""

ARCHITECTURE = "No component exists.\n"

CASES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("handoff", ("handoff",), HANDOFF),
    ("handoff_effort", ("handoff", "--effort", "alpha"), HANDOFF),
    ("view_plan", ("view", "plan"), PLAN),
    ("view_plan_effort", ("view", "plan", "--effort", "alpha"), PLAN),
    ("view_status", ("view", "status"), STATUS),
    ("view_verification", ("view", "verification"), VERIFICATION),
    ("view_roadmap", ("view", "roadmap"), ROADMAP),
    ("view_architecture_empty", ("view", "architecture"), ARCHITECTURE),
)


@pytest.fixture(scope="module")
def view_world(isolated_home: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = build_world(tmp_path_factory.mktemp("views"), wave_started=True)
    seed_view_records(root)
    return root


def normalized(text: str, root: Path) -> str:
    return re.sub(r"rec-[0-9a-f-]{36}", "rec-<id>", text.replace(str(root), "<root>"))


@pytest.mark.parametrize(
    ("argv", "recorded"),
    [pytest.param(argv, recorded, id=f"light_components-{name}") for name, argv, recorded in CASES],
)
def test_view_prints_recorded_text(argv: tuple[str, ...], recorded: str, view_world: Path) -> None:
    result = invoke("orchestra", list(argv), view_world)
    assert result.code == 0, result.err
    assert result.err == ""
    assert normalized(result.out, view_world) == recorded
