import json

from orchestra.sessions.session_tools import tool_metrics
from orchestra.sessions.session_types import JsonObject, JsonValue, TranscriptEvent


def use(tid: str, name: str, **inp: str) -> TranscriptEvent:
    tool_input: JsonObject = {}
    for key, value in inp.items():
        tool_input[key] = value
    item: JsonObject = {"type": "tool_use", "id": tid, "name": name, "input": tool_input}
    content: list[JsonValue] = [item]
    return {
        "type": "assistant",
        "message": JsonObject({"content": content}),
    }


def result(tid: str, is_error: bool = False, text: str = "SECRET") -> TranscriptEvent:
    item: JsonObject = {
        "type": "tool_result",
        "tool_use_id": tid,
        "content": text,
        "is_error": is_error,
    }
    content: list[JsonValue] = [item]
    return {
        "type": "user",
        "message": JsonObject({"content": content}),
    }


def fixture() -> list[TranscriptEvent]:
    return [
        use("1", "Bash", cmd="make"),
        result("1", True),
        use("2", "Bash", cmd="make"),
        result("2", False),
        use("3", "Read", path="a"),
        result("3", True),
        use("4", "Read", path="b"),
        result("4", False),
        use("5", "Edit", path="a"),
        result("5", False),
    ]


def test_counts_five_calls_two_errors_one_retry_per_tool():
    m = tool_metrics(fixture())
    assert m["tools"] == {
        "Bash": {"calls": 2, "errors": 1, "retries": 1},
        "Read": {"calls": 2, "errors": 1, "retries": 0},
        "Edit": {"calls": 1, "errors": 0, "retries": 0},
    }
    assert m["totals"] == {"calls": 5, "errors": 2, "retries": 1}


def test_repeat_without_prior_error_is_not_a_retry():
    events = [use("1", "Bash", cmd="x"), result("1"), use("2", "Bash", cmd="x"), result("2")]
    assert tool_metrics(events)["totals"]["retries"] == 0


def test_same_tool_different_input_is_not_a_retry():
    events = [use("1", "Bash", cmd="x"), result("1", True), use("2", "Bash", cmd="y"), result("2")]
    assert tool_metrics(events)["totals"]["retries"] == 0


def test_output_holds_no_input_or_result_text():
    out = json.dumps(tool_metrics(fixture()))
    assert "SECRET" not in out and "make" not in out


def test_unmatched_result_and_malformed_events_are_ignored():
    events = [
        result("zzz", True),
        {"type": "user"},
        {"message": {"content": "text"}},
        use("1", "Bash"),
    ]
    m = tool_metrics(events)
    assert m["totals"] == {"calls": 1, "errors": 0, "retries": 0}
