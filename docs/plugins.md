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
```

Install the distribution in the Orchestra environment:

```sh
python -m pip install .
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

## Verification plugins

Register a class that implements `VerificationTechnique` and a `run` method. The class must validate its configuration, declare its execution settings, return `TechniqueResult`, and validate its output.

```python
from orchestra.canon.project_config import ProjectConfig
from orchestra.canon.types import JsonObject
from orchestra.plugins import PluginContext
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

[verify.acme-checks]
runner = ["acme-check", "--strict"]
```

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

Orchestra passes the proof packet, base branch, remote, polling limits, and config in `LandRequest`. A result uses `success`, `fail`, `blocked`, or `skipped`. Orchestra keeps the human merge decision.
