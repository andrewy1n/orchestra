from tests.layout_support import ROOT


def _entries(component: str) -> set[str]:
    root = ROOT / "orchestra" / component
    return {path.name for path in root.iterdir() if path.name != "__pycache__"}


def test_score_root_holds_only_its_cli_lookups_and_the_model_packages():
    assert _entries("score") == {
        "__init__.py",
        "cli.py",
        "lookups.py",
        "facts",
        "planning",
        "schemas",
        "workflow",
    }


def test_tuner_root_holds_only_its_cli_plugin_verifier_and_the_packages():
    assert _entries("tuner") == {
        "__init__.py",
        "cli.py",
        "verify_plugins.py",
        "authoring",
        "evidence",
        "plugins",
        "schemas",
    }
