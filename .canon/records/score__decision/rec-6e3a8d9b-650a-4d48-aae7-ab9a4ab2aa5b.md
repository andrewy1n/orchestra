---
{
  "id": "rec-6e3a8d9b-650a-4d48-aae7-ab9a4ab2aa5b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "pytest adapter in Python; hardcoded pytest with a private JUnit report",
    "choice": "manifest argv template, JUnit XML report; absent runner is the shipped pytest template",
    "effort": "evidence-layer",
    "phase": "runner-adapter"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-17T23:34:26+00:00",
  "relationships": {},
  "revision": "sha256:b11052b4da7868d06bcd2dac1a3a1da2f96f8e169b55234922cdc7cdd5d821be",
  "subject": "runner-template",
  "time": {
    "as_of": "2026-10-17T23:34:26+00:00"
  }
}
---

## Rationale

The manifest carries an argv template, and the report is JUnit XML. `{tests}` is its own element and expands to the requested ids. `{report}` is the path of the XML file. The process is started from that list. When `runner` is absent, verdict uses the shipped pytest template, which forces `junit_family=xunit1` and writes `--junitxml`. A later runner is another template. `second-runner` can then judge a non-Python suite with no new affidavit module.

## Counter-argument

A pytest adapter in Python would keep node ids exact and would leave the command out of the manifest, so an agent could not swap the runner for a command that writes a passing report. The template puts that command in the committed file one phase before `frozen-environment` hashes it.
