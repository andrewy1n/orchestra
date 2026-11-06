# Plugin author guide

Orchestra discovers installed Python plugins through entry points. Install each plugin in the same environment as Orchestra. Plugin ids are unique within a scope. The same id can appear in another scope.

## Register a plugin

Add an entry point to the plugin distribution's `pyproject.toml`:

```toml
[project.entry-points."orchestra.tuner.verify"]
acme-checks = "acme_orchestra.verify:Technique"

[project.entry-points."orchestra.conductor.land"]
acme-land = "acme_orchestra.land:Adapter"

[project.entry-points."orchestra.composer.ideas"]
acme-ideas = "acme_orchestra.ideas:Source"

[project.entry-points."orchestra.plugin_api"]
v1 = "acme_orchestra.verify:Technique"

[project.entry-points."orchestra.plugin_config"]
"acme-checks__<base64url-schema>" = "acme_orchestra.verify:Technique"
"acme-land__<base64url-schema>" = "acme_orchestra.land:Adapter"
"acme-ideas__<base64url-schema>" = "acme_orchestra.ideas:Source"
```

Declare one `plugin_config` entry for every plugin id in the distribution. Encode its JSON object schema as unpadded URL-safe base64 in the entry name after `<plugin-id>__`. Orchestra checks `properties`, `required`, and `additionalProperties` against the matching table in `orchestra.toml`. The entry-point value must reference a Python object. Orchestra reads the API version from the `v1` entry name and rejects missing or unsupported versions.

Generate the encoded config name with Python:

```python
import base64
import json

schema = {"type": "object", "properties": {"project": {"type": "string"}}, "required": ["project"]}
encoded = base64.urlsafe_b64encode(
    json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
).decode("ascii").rstrip("=")
print(f"acme-ideas__{encoded}")
```

Install the distribution in the Orchestra environment:

```sh
python -m pip install .
```

The runnable example distribution is in `examples/third-party-plugins`:

```sh
python -m pip install ./examples/third-party-plugins
orchestra plugins list
```

List registered plugins without loading them:

```python
from orchestra.canon.extensions import list_plugins

for descriptor in list_plugins():
    print(descriptor.scope, descriptor.plugin_id, descriptor.target)
```

The CLI provides the same catalog view:

```sh
orchestra plugins list
orchestra plugins list --scope tuner.verify --format json
```

`list_plugins(scope)` filters by `composer.ideas`, `tuner.verify`, or `conductor.land`. `resolve_plugin(scope, plugin_id)` loads only the selected entry point. Orchestra rejects duplicate ids in one scope and API versions other than `1`.

## Idea-source plugins

Register idea sources in `orchestra.composer.ideas`. The interface returns structured items. It does not write ideas to the Canon store.

Implement the list operation with `IdeaSourceRequest` and `IdeaSourceItem`:

```python
from orchestra.composer.idea_source import IdeaSourceItem, IdeaSourceRequest


class Source:
    def list_ideas(self, request: IdeaSourceRequest) -> tuple[IdeaSourceItem, ...]:
        project = request.parameters["project"]
        return (
            IdeaSourceItem(
                external_id="issue-17",
                title="Add plugin discovery",
                body="Expose ideas from the configured project.",
                url=f"https://example.test/{project}/issues/17",
                updated_at="2026-11-03T09:00:00Z",
                labels=("orchestra",),
            ),
        )
```

Each item carries an external id, title, body, URL, ISO 8601 update time, and labels. `list_ideas` does not paginate, persist, or synchronize items. Issue #31 owns source ingestion and storage mapping.

Load and run a registered source through Orchestra's public interface:

```python
from orchestra.composer.idea_source import fetch_plugin_ideas

items = fetch_plugin_ideas("acme-ideas", {"project": "orchestra"})
```

## Verification plugins

Register a class that implements `VerificationTechnique` and a `run` method. The class must validate its configuration, declare its execution settings, return `TechniqueResult`, and validate its output.

```python
from orchestra.canon.project_config import ProjectConfig
from orchestra.canon.types import JsonObject
from orchestra.tuner.plugins import PluginContext
from orchestra.tuner.technique import TechniqueResult


class Technique:
    def validate_config(self, config: ProjectConfig) -> None:
        if "acme-checks" not in config.verify_config:
            raise ValueError("acme-checks configuration is missing")

    def execution_definition(self, config: ProjectConfig) -> JsonObject:
        return {
            "engine": "acme-checks-v1",
            "runner_argv": list(config.verify_config["acme-checks"]["runner"]),
        }

    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult:
        del config
        return TechniqueResult("pass", {"revision": context.revision})

    def validate_result(self, result: TechniqueResult) -> None:
        if not isinstance(result.output.get("revision"), str):
            raise ValueError("revision output is required")
```

Configure a stage and plugin parameters in the target repository's `orchestra.toml`:

```toml
[verify.stages]
phase = ["acme-checks"]

[verify.unit]
runner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]

[verify.acme-checks]
runner = ["acme-check", "--strict"]
```

The example distribution registers `example-checks` and provides a replay implementation. Use its id to try the installed package.

## Wrapping a CLI

A plugin that runs an external program imports from `orchestra.tools`. Do not call `subprocess` directly.

Subclass `CliTool`. Set `executable` and `min_version`. `CliTool` checks the version on the first command and raises `ToolVersionError` when the installed program is older than `min_version`. Call `self.require(version, feature)` at the start of one method to gate it on a newer version.

Every failure is a `ToolError`: a missing executable, a timeout, a non-zero exit, or invalid JSON. Subclasses catch nothing.

A method returns a frozen dataclass. It parses the output of `self._text(...)` or `self._json(...)`, so callers never see raw argv or JSON.

```python
from dataclasses import dataclass
from pathlib import Path

from orchestra.tools import CliTool, ToolError, Version


@dataclass(frozen=True)
class Status:
    branch: str
    dirty: bool


class MyTool(CliTool):
    executable = "mytool"
    min_version = Version(1, 2)

    def status(self) -> Status:
        raw = self._json("status", "--json")
        if not isinstance(raw, dict):
            raise ToolError("unexpected status output", [self.executable, "status"], None, "")
        return Status(branch=str(raw["branch"]), dirty=bool(raw["dirty"]))

    def prune(self) -> str:
        self.require(Version(1, 5), "prune")
        return self._text("prune")
```

Tests inject a fake runner through `run=`. `scripted(MyTool, responses)` answers `mytool --version` with `min_version`, answers each key in `responses` with its text, and fails on any other call. Pass `version=` to script a different version.

```python
import pytest

from orchestra.tools import ToolVersionError
from orchestra.tools.testing import scripted


def test_status_parses_json() -> None:
    run = scripted(MyTool, {("mytool", "status", "--json"): '{"branch": "main", "dirty": false}'})
    assert MyTool(Path("."), run=run).status() == Status(branch="main", dirty=False)


def test_prune_needs_newer_version() -> None:
    run = scripted(MyTool, {("mytool", "prune"): "ok"})
    with pytest.raises(ToolVersionError):
        MyTool(Path("."), run=run).prune()
```

## Landing plugins

Configure a landing adapter explicitly. Missing `[land]` settings raise an error when you run `orchestra land`.

```toml
[land]
adapter = "github-pr"
merge = "human"

[land.config]
repository = "acme/orchestra"
```

The built-in GitHub adapter uses the authenticated `gh` CLI. It needs no token variable. It needs `gh` 2.50.0 or newer. When you set `repository`, the adapter passes it as `-R owner/repo`. Otherwise `gh` reads the git remote.

Every plugin returns one of `pass`, `fail`, `error`, or `skip`, with JSON object output. The plugin declares every setting that affects execution in `execution_definition`. Orchestra binds that definition, the committed parameters, entry point target, distribution metadata, scope, id, and API version into signed evidence.

Claim replay is optional. To support it, add `replay(request)` and return one outcome for each requested test id. Outcomes are `passed`, `assertion_failed`, `errored`, or `not_run`. Configure `[verify.replay] technique = "acme-checks"` only when the technique supports replay.

Orchestra validates output before signing. Plugins do not receive signing keys. The declared identity does not hash installed source files or dependencies.

## Landing plugins

Register a class that implements `LandAdapter.run(request)` and returns `LandingResult`:

```python
from orchestra.conductor.land import LandRequest, LandingResult


class Adapter:
    def run(self, request: LandRequest) -> LandingResult:
        return LandingResult(
            result="success",
            number=17,
            url="https://example.test/pull/17",
            head_sha="abc123",
            checks=(),
            statuses=("ready",),
        )
```

Select the adapter in `orchestra.toml` and pass adapter settings under `land.config`:

```toml
[land]
adapter = "acme-land"
merge = "human"

[land.config]
region = "west"
```

The example `example-land` adapter returns `skipped`. It checks the dispatch contract without opening a pull request.

Orchestra passes the proof packet, base branch, remote, polling limits, and config in `LandRequest`. A result uses `success`, `fail`, `blocked`, or `skipped`. Orchestra keeps the human merge decision.
