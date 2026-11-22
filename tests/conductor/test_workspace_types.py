from __future__ import annotations

from orchestra.conductor.workspace_types import (
    ASSESSMENT_TYPE,
    INTEGRATION_REPORT_TYPE,
    RELEASE_TYPE,
)


def test_record_type_names_are_conductor_schema_types() -> None:
    assert (ASSESSMENT_TYPE, INTEGRATION_REPORT_TYPE, RELEASE_TYPE) == (
        "conductor:assessment",
        "conductor:integration-report",
        "conductor:release",
    )
