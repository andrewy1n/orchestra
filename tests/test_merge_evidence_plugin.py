from pathlib import Path

from orchestra.canon.extensions import PLUGIN_GROUPS
from orchestra.canon.project_config import load_project_config


def test_ci_evidence_selects_a_plugin_independently_of_landing(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        """
[verify.stages]
task = ["unit"]
[verify.unit]
runner = ["pytest", "{tests}", "{report}"]
[land]
adapter = "github-pr"
[merge_evidence]
adapter = "other-ci"
[merge_evidence.config]
repository = "example/project"
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert config.land_adapter == "github-pr"
    assert config.merge_evidence_adapter == "other-ci"
    assert config.merge_evidence_config == {"repository": "example/project"}


def test_ci_evidence_has_its_own_plugin_group() -> None:
    assert "orchestra.conductor.merge_evidence" in PLUGIN_GROUPS.values()
