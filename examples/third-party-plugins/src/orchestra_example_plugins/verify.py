from __future__ import annotations

from collections.abc import Mapping

from orchestra.canon.project_config import ProjectConfig
from orchestra.canon.types import JsonObject
from orchestra.plugins import PluginContext
from orchestra.tuner.technique import (
    ReplayRequest,
    TechniqueResult,
    TestOutcome,
)


class Technique:
    def validate_config(self, config: ProjectConfig) -> None:
        options = config.verify_config.get("example-checks", {})
        enabled = options.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")

    def execution_definition(self, config: ProjectConfig) -> JsonObject:
        del config
        return {"engine": "example-checks-v1"}

    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult:
        del config
        return TechniqueResult("pass", {"revision": context.revision, "tests": list(context.tests)})

    def validate_result(self, result: TechniqueResult) -> None:
        if not isinstance(result.output.get("revision"), str):
            raise ValueError("revision is required")
        tests = result.output.get("tests")
        if not isinstance(tests, list) or any(not isinstance(test, str) for test in tests):
            raise ValueError("tests must be a string list")

    def replay(self, request: ReplayRequest) -> Mapping[str, TestOutcome]:
        return {test_id: "passed" for test_id in request.test_ids}
