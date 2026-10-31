"""Oracles for the UI structure phase: dashboard/frontend, $lib alias, shadcn-svelte, split App.svelte."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = REPO_ROOT / "dashboard"
FRONTEND = DASHBOARD / "frontend"
SRC = FRONTEND / "src"
LIB = SRC / "lib"
APP_SVELTE = SRC / "App.svelte"

STATE_MODULES = ("polling.svelte.ts", "journal.svelte.ts", "overlay.svelte.ts")
SCREENS = ("Home.svelte", "Journal.svelte", "Overlay.svelte", "SideRail.svelte")
RUNE = re.compile(r"\$(state|derived)\b")
LINK_TEST_HASHES = {
    "deepLinks.test.ts": "3841d5e7798686781eacc774cefa982348c13ad64b17a19d5af0e09d9cc0ba96",
    "links.test.ts": "8ccf7a8cd49bb076eaa7bdb5590a1a7335b56e3148f3e41279a7970c12f61c8e",
}
JSONC_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.DOTALL)


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def require_file(path: Path) -> str:
    assert path.is_file(), f"missing {relative(path)}"
    return path.read_text()


def parse_jsonc(text: str) -> dict:
    stripped = JSONC_TOKEN.sub(
        lambda match: match.group(0) if match.group(0).startswith('"') else "", text
    )
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", stripped))


def svelte_sources_outside_ui_components() -> list[Path]:
    ui_components = LIB / "components" / "ui"
    return [path for path in sorted(SRC.rglob("*.svelte")) if ui_components not in path.parents]


def test_r1_ui_lives_in_dashboard_frontend_and_dashboard_web_is_gone():
    assert (FRONTEND / "package.json").is_file(), "missing dashboard/frontend/package.json"
    assert not (DASHBOARD / "web").exists(), "dashboard/web still exists"


def test_r2_server_serves_dashboard_frontend_dist():
    app = importlib.import_module("dashboard.backend.server.app")
    assert Path(app.DIST) == REPO_ROOT / "dashboard" / "frontend" / "dist"


def test_r3_app_svelte_has_fewer_than_150_lines():
    lines = require_file(APP_SVELTE).splitlines()
    assert len(lines) < 150, f"App.svelte has {len(lines)} lines"


def test_r4_polling_journal_and_overlay_state_live_in_svelte_ts_modules():
    state_dir = LIB / "state"
    assert state_dir.is_dir(), f"missing {relative(state_dir)}"
    for name in STATE_MODULES:
        text = require_file(state_dir / name)
        assert RUNE.search(text), f"{name} has no $state or $derived rune"


def test_r5_home_journal_overlay_and_side_rail_are_components_under_lib():
    screens_dir = LIB / "screens"
    app = require_file(APP_SVELTE)
    for name in SCREENS:
        text = require_file(screens_dir / name)
        assert text.strip(), f"{name} is empty"
        assert re.search(rf"import\s[^;]*['\"][^'\"]*{re.escape(name)}['\"]", app), (
            f"App.svelte does not import {name}"
        )


def test_r6_components_json_aliases_point_at_lib():
    config = json.loads(require_file(FRONTEND / "components.json"))
    aliases = config.get("aliases")
    assert isinstance(aliases, dict) and aliases, "components.json has no aliases"
    for key in ("components", "utils", "ui", "hooks"):
        assert key in aliases, f"aliases.{key} is missing"
    for key, value in aliases.items():
        assert str(value).startswith("$lib"), f"aliases.{key} is {value!r}"


def test_r7_lib_alias_resolves_in_vite_and_tsconfig():
    vite = require_file(FRONTEND / "vite.config.ts")
    assert "$lib" in vite, "vite.config.ts does not mention $lib"
    assert re.search(r"\balias\b", vite), "vite.config.ts has no alias mapping"
    tsconfig = parse_jsonc(require_file(FRONTEND / "tsconfig.app.json"))
    paths = tsconfig.get("compilerOptions", {}).get("paths", {})
    assert {"$lib", "$lib/*"} & set(paths), f"tsconfig paths lack $lib: {sorted(paths)}"


def test_r8_overlay_tabs_and_dialogs_import_shadcn_components():
    ui_components = LIB / "components" / "ui"
    for name in ("tabs", "dialog"):
        assert (ui_components / name).is_dir(), f"missing {relative(ui_components / name)}"
        pattern = re.compile(rf"""from\s+['"]\$lib/components/ui/{name}(?:/[^'"]*)?['"]""")
        users = [
            path
            for path in svelte_sources_outside_ui_components()
            if pattern.search(path.read_text())
        ]
        assert users, f"no .svelte file imports $lib/components/ui/{name}"


def test_r9_global_css_defines_the_shadcn_theme_variables():
    css = require_file(SRC / "app.css")
    root = re.search(r":root\s*\{(.*?)\n\}", css, re.DOTALL)
    dark = re.search(r"\.dark\s*\{(.*?)\n\}", css, re.DOTALL)
    assert root, "app.css has no :root block"
    assert dark, "app.css has no .dark block"
    for variable in ("--background", "--foreground", "--primary", "--border", "--radius"):
        assert re.search(rf"{re.escape(variable)}\s*:", root.group(1)), f":root lacks {variable}"
    assert re.search(r"--background\s*:", dark.group(1)), ".dark lacks --background"


def test_r12_link_and_deep_link_tests_are_unchanged():
    for name, expected in LINK_TEST_HASHES.items():
        path = SRC / name
        assert path.is_file(), f"missing {relative(path)}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected, f"{name} changed: {digest}"
