import ast
import importlib
from pathlib import Path

import orchestra.conductor


def _conductor_modules_defining(class_name: str) -> list[str]:
    root = Path(orchestra.conductor.__file__).parent
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text())
        if any(
            isinstance(node, ast.ClassDef) and node.name == class_name for node in ast.walk(tree)
        ):
            found.append(path.name)
    return found


def test_no_conductor_module_defines_github_gh() -> None:
    assert _conductor_modules_defining("GitHubGh") == []


def test_github_gh_lives_in_tools() -> None:
    module = importlib.import_module("orchestra.tools.github")
    assert module.GitHubGh.__module__ == "orchestra.tools.github"
