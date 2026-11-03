from __future__ import annotations

import re
from pathlib import Path


def test_plugin_author_guide_covers_each_scope_and_compiles_python_examples() -> None:
    guide = Path(__file__).parents[1] / "docs" / "plugins.md"
    content = guide.read_text(encoding="utf-8")

    for required_text in (
        "orchestra.composer.ideas",
        "orchestra.tuner.verify",
        "orchestra.conductor.land",
        "IdeaSourceRequest",
        "IdeaSourceItem",
        "list_ideas",
        "VerificationTechnique",
        "TechniqueResult",
        "LandAdapter",
        "LandingResult",
        "orchestra plugins list",
        "[verify.stages]",
        "[land.config]",
    ):
        assert required_text in content

    examples = re.findall(r"```python\n(.*?)```", content, flags=re.DOTALL)
    assert len(examples) == 4
    for index, example in enumerate(examples):
        compile(example, f"plugin-guide-{index}.py", "exec")
