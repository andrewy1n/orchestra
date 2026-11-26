"""Tests for the product overview sections of orchestra view roadmap."""

from __future__ import annotations

import json

from test_roadmap_view import _create_area, roadmap, run_orchestra

PURPOSE = "Keep delivery work legible"
AUDIENCE = "maintainers of small teams"


def _create(cli, record_type: str, subject: str, payload: dict) -> dict:
    result = cli(
        "create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def _statement(cli, purpose: str = PURPOSE, audience: str = AUDIENCE) -> dict:
    return _create(cli, "composer:product", "product", {"purpose": purpose, "audience": audience})


def _item(cli, subject: str, status: str, title: str | None = None) -> dict:
    return _create(
        cli,
        "composer:product-item",
        subject,
        {"title": title or f"Title {subject}", "description": f"Text {subject}", "status": status},
    )


def _line_with(text: str, needle: str) -> str:
    return next(line for line in text.splitlines() if needle in line)


def test_roadmap_groups_statement_then_capabilities_then_goals(store, cli):
    _statement(cli)
    _item(cli, "ships-now", "current")
    _item(cli, "comes-later", "planned")
    text = roadmap(store)
    assert PURPOSE in text and AUDIENCE in text
    statement_at = text.index(PURPOSE)
    capabilities_at = text.index("Capabilities")
    goals_at = text.index("Goals")
    assert statement_at < capabilities_at < goals_at
    capabilities = text[capabilities_at:goals_at]
    goals = text[goals_at:]
    assert "Title ships-now" in capabilities
    assert "Title comes-later" not in capabilities
    assert "Title comes-later" in goals
    assert "Title ships-now" not in goals
    assert "current" in _line_with(capabilities, "Title ships-now")
    assert "planned" in _line_with(goals, "Title comes-later")


def test_roadmap_groups_put_product_before_areas(store, cli):
    _create_area(cli, "dashboard")
    _statement(cli)
    _item(cli, "ships-now", "current")
    text = roadmap(store)
    assert text.index(PURPOSE) < text.index("Capabilities") < text.index("## dashboard")


def test_roadmap_supersede_goal_to_capability_shows_only_capability(store, cli):
    _item(cli, "export", "planned")
    result = cli(
        "supersede",
        "--type",
        "composer:product-item",
        "--subject",
        "export",
        "--payload",
        json.dumps({"status": "current"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    text = roadmap(store)
    assert text.count("Title export") == 1
    capabilities_at = text.index("Capabilities")
    goals_at = text.index("Goals")
    assert capabilities_at < text.index("Title export") < goals_at
    assert "planned" not in _line_with(text, "Title export")
    listed = cli("list", "--type", "composer:product-item", "--subject", "export")
    assert listed.returncode == 0, listed.stdout + listed.stderr
    assert "planned" in listed.stdout and "current" in listed.stdout


def test_roadmap_no_statement_says_so_and_shows_none(store, cli):
    _item(cli, "ships-now", "current")
    text = roadmap(store)
    assert "No product statement" in text
    assert "None" not in text
    assert "Purpose" not in text.split("Capabilities")[0].replace("No product statement", "")


def test_roadmap_no_statement_and_no_items_still_says_so(store, cli):
    text = roadmap(store)
    assert "No product statement" in text


def test_overview_is_one_per_project_not_per_area(store, cli):
    _create_area(cli, "dashboard")
    _create_area(cli, "cli")
    _statement(cli)
    _item(cli, "ships-now", "current")
    _item(cli, "comes-later", "planned")
    text = roadmap(store)
    assert text.count(PURPOSE) == 1
    assert text.count("## Capabilities") == 1
    assert text.count("## Goals") == 1
    assert text.index("## Goals") < text.index("## dashboard")
    assert "Title ships-now" in text[text.index("## Capabilities") : text.index("## Goals")]
    assert "Title comes-later" in text[text.index("## Goals") : text.index("## cli")]


def test_roadmap_fails_loudly_for_a_statement_with_the_wrong_subject(store, cli):
    _create(cli, "composer:product", "elsewhere", {"purpose": PURPOSE, "audience": AUDIENCE})
    result = run_orchestra(store, "view", "roadmap")
    assert result.returncode != 0
    assert "subject product" in result.stdout + result.stderr
