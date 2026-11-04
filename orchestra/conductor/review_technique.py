from __future__ import annotations

from orchestra.canon.project_config import ProjectConfig
from orchestra.canon.types import JsonObject
from orchestra.conductor.reviewer import validate_reviewer_output
from orchestra.tuner.plugins import PluginContext
from orchestra.tuner.technique import TechniqueResult


class ReviewTechnique:
    def validate_config(self, config: ProjectConfig) -> None:
        del config

    def execution_definition(self, config: ProjectConfig) -> JsonObject:
        del config
        return {"reviewer_contract": 1}

    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult:
        del config
        if context.reviewer_output is None or not context.reviewer_output.strip():
            raise ValueError("review plugin requires structured output from the host reviewer")
        parsed = validate_reviewer_output(context.reviewer_output)
        verdict = parsed["verdict"]
        return TechniqueResult(
            verdict="pass" if verdict == "PASS" else "fail",
            output={"verdict": verdict, "reviewer_output": context.reviewer_output},
        )

    def validate_result(self, result: TechniqueResult) -> None:
        verdict = result.output.get("verdict")
        reviewer_output = result.output.get("reviewer_output")
        if verdict not in ("PASS", "NEEDS_WORK") or not isinstance(reviewer_output, str):
            raise ValueError("review plugin output does not contain a valid reviewer result")
        try:
            parsed = validate_reviewer_output(reviewer_output)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "review plugin output does not contain a valid reviewer result"
            ) from exc
        if (result.verdict == "pass") != (verdict == "PASS") or parsed["verdict"] != verdict:
            raise ValueError("review plugin verdict does not match the reviewer result")
