from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "wheel_smoke.py"
_TRACE_VERSION = "1"
_LOCK_PATH = Path(tempfile.gettempdir()) / "orchestra-wheel-smoke.lock"
_VALUE_OPTIONS = {
    "-p",
    "--python",
    "--prompt",
    "--directory",
    "--project",
    "--prefix",
    "--target",
    "--out-dir",
    "-o",
    "--package",
    "--python-version",
    "--python-platform",
    "--index",
    "--default-index",
    "-i",
    "--index-url",
    "--extra-index-url",
    "-f",
    "--find-links",
    "--cache-dir",
    "--config-file",
    "--color",
    "--allow-insecure-host",
    "--link-mode",
    "--index-strategy",
    "--keyring-provider",
    "--exclude-newer",
    "--exclude-newer-package",
    "--refresh-package",
    "--resolution",
    "--upgrade-package",
    "--build-constraints",
    "--constraints",
    "--overrides",
    "--excludes",
    "--extra",
    "--group",
    "--requirements",
    "-r",
    "--editable",
    "-e",
}

_RUNNER = r"""
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

trace_path, script, *script_args = sys.argv[1:]
events = []
cwd_now = [os.getcwd()]
real_run = subprocess.run
real_call = subprocess.call
real_chdir = os.chdir
real_system = os.system

VALUE_OPTIONS = set(""" + repr(sorted(_VALUE_OPTIONS)) + r""")


def clip(data, limit=65536):
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data[:limit].decode(errors="replace")
    return str(data)[:limit]


def option(tokens, names):
    for index, token in enumerate(tokens):
        for name in names:
            if token == name and index + 1 < len(tokens):
                return tokens[index + 1]
            prefix = name + "="
            if token.startswith(prefix):
                return token[len(prefix) :]
    return None


def positionals(tokens, marker):
    found = False
    skip = False
    values = []
    for token in tokens:
        if not found:
            if token == marker:
                found = True
            continue
        if skip:
            skip = False
            continue
        if token in VALUE_OPTIONS:
            skip = True
            continue
        if token.startswith("-"):
            continue
        values.append(token)
    return values


def pyvenv_root(path):
    if not path:
        return None
    current = Path(path)
    if not current.is_absolute():
        current = Path(cwd_now[0]) / current
    try:
        if current.is_symlink() or current.is_file():
            current = current.parent
    except OSError:
        return None
    for parent in [current, *current.parents]:
        if (parent / "pyvenv.cfg").is_file():
            try:
                return str(parent.resolve())
            except OSError:
                return str(parent)
    return None


def created_venv(tokens, cwd, returncode):
    if returncode != 0:
        return None
    names = [Path(token).name for token in tokens]
    directory = option(tokens, {"--directory"}) or cwd
    target = None
    if "uv" in names and "venv" in tokens:
        found = positionals(tokens, "venv")
        target = found[0] if found else str(Path(directory) / ".venv")
        if not os.path.isabs(target):
            target = os.path.join(directory, target)
    elif "-m" in tokens and "venv" in tokens:
        found = positionals(tokens, "venv")
        if not found:
            return None
        target = found[0]
        if not os.path.isabs(target):
            target = os.path.join(cwd, target)
    if target and os.path.isfile(os.path.join(target, "pyvenv.cfg")):
        return os.path.abspath(target)
    return None


def venv_root(tokens, cwd, env, resolved):
    candidates = []
    virtual = env.get("VIRTUAL_ENV") if env else None
    if virtual:
        candidates.append(virtual)
    chosen = option(tokens, {"-p", "--python"})
    if chosen:
        candidates.append(chosen if os.path.isabs(chosen) else os.path.join(cwd, chosen))
    prefix = option(tokens, {"--prefix"})
    if prefix:
        candidates.append(prefix if os.path.isabs(prefix) else os.path.join(cwd, prefix))
    if resolved:
        candidates.append(resolved)
    for candidate in candidates:
        root = pyvenv_root(candidate)
        if root:
            return root
    return None


def resolve(argv0, env, cwd):
    if not argv0:
        return ""
    if os.path.isabs(argv0) or os.sep in argv0:
        path = argv0 if os.path.isabs(argv0) else os.path.join(cwd, argv0)
        return os.path.abspath(path)
    search = env.get("PATH", "") if env is not None else ""
    for entry in search.split(os.pathsep):
        candidate = os.path.join(entry, argv0)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return os.path.abspath(candidate)
    return argv0


def command_tokens(argv, shell):
    if shell and len(argv) == 1:
        try:
            return __import__("shlex").split(argv[0])
        except ValueError:
            return argv[0].split()
    return argv


def record(args, kwargs, result):
    shell = bool(kwargs.get("shell"))
    if isinstance(args, (str, bytes)):
        argv = [args.decode(errors="replace") if isinstance(args, bytes) else args]
        shell = True
    elif isinstance(args, (list, tuple)):
        argv = [os.fsdecode(part) if isinstance(part, bytes) else str(part) for part in args]
    else:
        argv = [str(args)]
    raw_cwd = kwargs.get("cwd")
    if raw_cwd is None:
        effective = cwd_now[0]
    else:
        effective = raw_cwd if os.path.isabs(str(raw_cwd)) else os.path.join(cwd_now[0], str(raw_cwd))
    effective = os.path.abspath(effective)
    env = kwargs.get("env")
    if env is None:
        env = os.environ
    resolved = resolve(argv[0] if argv else "", env, effective)
    tokens = command_tokens(argv, shell)
    text_parts = ["\n".join(argv)]
    for arg in argv:
        if not str(arg).endswith(".py"):
            continue
        path = arg if os.path.isabs(arg) else os.path.join(effective, arg)
        if os.path.isfile(path) and os.path.getsize(path) < 100000:
            text_parts.append(Path(path).read_text(errors="replace"))
    returncode = result.returncode if isinstance(result.returncode, int) else 1
    events.append(
        {
            "argv": argv,
            "shell": shell,
            "cwd": effective,
            "returncode": returncode,
            "stdout": clip(result.stdout),
            "stderr": clip(result.stderr),
            "pythonpath": env.get("PYTHONPATH", "") if env else "",
            "resolved": resolved,
            "venv_root": venv_root(tokens, effective, env, resolved),
            "created_venv": created_venv(tokens, effective, returncode),
            "is_git": os.path.exists(os.path.join(effective, ".git")),
            "text": "\n".join(text_parts),
        }
    )


def traced_run(*popenargs, **kwargs):
    kwargs = dict(kwargs)
    args = popenargs[0] if popenargs else kwargs.get("args")
    check = bool(kwargs.pop("check", False))
    injected = False
    if not kwargs.get("capture_output") and kwargs.get("stdout") is None:
        kwargs["stdout"] = subprocess.PIPE
        if kwargs.get("stderr") is None:
            kwargs["stderr"] = subprocess.PIPE
        injected = True
    kwargs["check"] = False
    result = real_run(*popenargs, **kwargs)
    record(args, kwargs, result)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, args, result.stdout, result.stderr)
    if injected:
        return subprocess.CompletedProcess(result.args, result.returncode)
    return result


def traced_call(*popenargs, **kwargs):
    result = traced_run(*popenargs, **kwargs)
    return result.returncode


def traced_check_call(*popenargs, **kwargs):
    returncode = traced_call(*popenargs, **kwargs)
    if returncode:
        command = popenargs[0] if popenargs else kwargs.get("args")
        raise subprocess.CalledProcessError(returncode, command)
    return 0


def traced_check_output(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    timeout = kwargs.pop("timeout", None)
    result = traced_run(*popenargs, stdout=subprocess.PIPE, timeout=timeout, check=True, **kwargs)
    return result.stdout


def traced_system(command):
    result = real_run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record([command], {"shell": True, "cwd": None, "env": None}, result)
    return result.returncode << 8


def traced_chdir(path):
    real_chdir(path)
    cwd_now[0] = os.getcwd()


subprocess.run = traced_run
subprocess.call = traced_call
subprocess.check_call = traced_check_call
subprocess.check_output = traced_check_output
os.system = traced_system
os.chdir = traced_chdir

code = 1
try:
    sys.argv = [script, *script_args]
    sys.path.insert(0, str(Path(script).resolve().parent))
    import runpy

    runpy.run_path(script, run_name="__main__")
    code = 0
except SystemExit as exc:
    if exc.code is None or exc.code == 0:
        code = 0
    elif isinstance(exc.code, int):
        code = exc.code
    else:
        code = 1
except Exception:
    traceback.print_exc()
    code = 1
finally:
    Path(trace_path).write_text(json.dumps({"events": events}))
raise SystemExit(code)
"""


def _script() -> Path:
    assert SCRIPT.is_file(), "missing scripts/wheel_smoke.py"
    return SCRIPT


def _fake_dist() -> Path:
    dist = Path(tempfile.mkdtemp(prefix="wheel-smoke-dist-")) / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>fake dist</title>")
    (dist / "assets" / "app.js").write_text("console.log('app');\n")
    return dist


def _run(command: list[str], *, cwd: Path, text: bool = True, input_bytes: bytes | None = None):
    proc = subprocess.run(
        command,
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
        text=text,
        check=False,
    )
    detail = proc.stderr or proc.stdout or ""
    if isinstance(detail, bytes):
        detail = detail.decode(errors="replace")
    assert proc.returncode == 0, detail[-2000:]
    return proc


def _head() -> str:
    proc = _run(["git", "rev-parse", "HEAD"], cwd=ROOT)
    return proc.stdout.strip()


def _porcelain() -> str:
    proc = _run(["git", "status", "--porcelain"], cwd=ROOT)
    return proc.stdout


def _lock():
    import fcntl

    class _Held:
        def __enter__(self):
            self._handle = _LOCK_PATH.open("a+")
            fcntl.flock(self._handle, fcntl.LOCK_EX)
            return self

        def __exit__(self, *_args):
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()

    return _Held()


def _under_root(entry: str) -> bool:
    if not entry:
        return False
    try:
        path = Path(entry).resolve()
    except OSError:
        return False
    root = ROOT.resolve()
    return path == root or root in path.parents


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = [
        entry
        for entry in env.get("PYTHONPATH", "").split(os.pathsep)
        if entry and not _under_root(entry)
    ]
    if pythonpath:
        env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    else:
        env.pop("PYTHONPATH", None)
    path = []
    root = str(ROOT.resolve())
    for entry in env.get("PATH", "").split(os.pathsep):
        if _under_root(entry):
            continue
        canon = Path(entry) / "canon"
        if canon.is_file():
            try:
                body = canon.read_text(errors="replace")
            except OSError:
                body = ""
            if root in body and "orchestra.canon" in body:
                continue
        path.append(entry)
    env["PATH"] = os.pathsep.join(path)
    for name in (
        "VIRTUAL_ENV",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "CANON_SCHEMA_PATH",
        "PYTHONHOME",
    ):
        env.pop(name, None)
    return env


def _invoke_unlocked(args: list[str]) -> dict:
    script = _script()
    work = Path(tempfile.mkdtemp(prefix="wheel-smoke-run-"))
    trace = work / "trace.json"
    runner = work / "runner.py"
    runner.write_text(_RUNNER)
    try:
        try:
            proc = subprocess.run(
                [sys.executable, str(runner), str(trace), str(script), *args],
                cwd=ROOT,
                env=_clean_env(),
                capture_output=True,
                text=True,
                check=False,
                timeout=900,
            )
        except subprocess.TimeoutExpired:
            assert False, "scripts/wheel_smoke.py timed out"
        detail = (proc.stderr or proc.stdout or "no trace")[-2000:]
        assert trace.is_file(), detail
        try:
            payload = json.loads(trace.read_text())
        except json.JSONDecodeError as exc:
            assert False, str(exc)
        assert isinstance(payload.get("events"), list), "trace has no events"
        payload["returncode"] = proc.returncode
        payload["stdout"] = proc.stdout
        payload["stderr"] = proc.stderr
        return payload
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _invoke(args: list[str]) -> dict:
    _script()
    with _lock():
        return _invoke_unlocked(args)


def _default_outcome() -> dict:
    script = _script()
    key = _TRACE_VERSION + hashlib.sha256(script.read_bytes()).hexdigest() + _head()
    path = Path(tempfile.gettempdir()) / f"orchestra-wheel-smoke-{key[:24]}.json"
    with _lock():
        if path.is_file():
            try:
                cached = json.loads(path.read_text())
            except json.JSONDecodeError:
                cached = None
            if isinstance(cached, dict) and cached.get("key") == key and isinstance(cached.get("events"), list):
                return cached
        before = _porcelain()
        dist = _fake_dist()
        try:
            outcome = _invoke_unlocked(["--dist", str(dist)])
        finally:
            shutil.rmtree(dist.parent, ignore_errors=True)
        after = _porcelain()
        outcome["before"] = before
        outcome["after"] = after
        outcome["key"] = key
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(outcome))
        os.replace(temporary, path)
        return outcome


def _events() -> list[dict]:
    return _default_outcome()["events"]


def _tail(outcome: dict) -> str:
    text = (outcome.get("stderr") or outcome.get("stdout") or "").strip()
    return text[-2000:]


def _built_wheel() -> Path:
    _script()
    dest = Path(tempfile.gettempdir()) / f"orchestra-wheel-smoke-{_head()}.whl"
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    with _lock():
        if dest.is_file() and dest.stat().st_size > 0:
            return dest
        work = Path(tempfile.mkdtemp(prefix="wheel-smoke-src-"))
        try:
            source = work / "source"
            source.mkdir()
            archived = subprocess.run(
                ["git", "archive", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            assert archived.returncode == 0, archived.stderr.decode(errors="replace")[-2000:]
            extracted = subprocess.run(
                ["tar", "-x", "-C", str(source)],
                input=archived.stdout,
                capture_output=True,
                check=False,
            )
            assert extracted.returncode == 0, extracted.stderr.decode(errors="replace")[-2000:]
            fake = _fake_dist()
            try:
                shutil.copytree(fake, source / "dashboard" / "frontend" / "dist")
            finally:
                shutil.rmtree(fake.parent, ignore_errors=True)
            built = subprocess.run(
                ["uv", "build", "--wheel"],
                cwd=source,
                capture_output=True,
                text=True,
                check=False,
            )
            assert built.returncode == 0, (built.stderr or built.stdout)[-2000:]
            wheels = sorted((source / "dist").glob("*.whl"))
            assert len(wheels) == 1, [str(path) for path in wheels]
            partial = dest.with_suffix(".whl.partial")
            partial.write_bytes(wheels[0].read_bytes())
            os.replace(partial, dest)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return dest


def _strip_providers(wheel: Path) -> Path:
    assert zipfile.is_zipfile(wheel), wheel
    dest = Path(tempfile.mkdtemp(prefix="wheel-smoke-stripped-")) / "stripped.whl"
    found = False
    with zipfile.ZipFile(wheel) as source, zipfile.ZipFile(dest, "w") as output:
        for info in source.infolist():
            if info.filename.endswith("installer/providers.json"):
                found = True
                continue
            output.writestr(info, source.read(info.filename))
    assert found, "providers.json was not in the wheel"
    return dest


def _tokens(event: dict) -> list[str]:
    argv = [str(part) for part in event.get("argv") or []]
    if event.get("shell") and len(argv) == 1:
        try:
            return shlex.split(argv[0])
        except ValueError:
            return argv[0].split()
    return argv


def _names(tokens: list[str]) -> list[str]:
    return [Path(token).name for token in tokens]


def _is_uv(tokens: list[str]) -> bool:
    return "uv" in _names(tokens)


def _is_uv_build_wheel(event: dict) -> bool:
    tokens = _tokens(event)
    return _is_uv(tokens) and "build" in tokens and "--wheel" in tokens


def _is_build(event: dict) -> bool:
    tokens = _tokens(event)
    names = _names(tokens)
    if "uv" in names and "build" in tokens:
        return True
    if "-m" in tokens and "build" in tokens:
        return True
    return any(name == "pip" or name.startswith("pip") for name in names) and "wheel" in tokens


def _is_wheel_install(event: dict) -> bool:
    tokens = _tokens(event)
    if "install" not in tokens or not any(".whl" in token for token in tokens):
        return False
    names = _names(tokens)
    return "uv" in names or "pip" in names or any(name.startswith("pip") for name in names)


def _outside(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    root = ROOT.resolve()
    return resolved != root and root not in resolved.parents


def _is_orchestra(tokens: list[str]) -> bool:
    if "orchestra" in _names(tokens):
        return True
    return "-m" in tokens and ("orchestra" in tokens or "orchestra.cli" in tokens)


def _is_canon(tokens: list[str]) -> bool:
    if "canon" in _names(tokens):
        return True
    return "-m" in tokens and ("orchestra.canon" in tokens or "canon" in tokens)


def _imports(text: str, module: str) -> bool:
    name = re.escape(module)
    direct = rf"(?:^|\s|;)(?:import\s+(?:[\w.]+\s*,\s*)*|from\s+){name}(?!\.\w)"
    call = f"(?:__import__|import_module)\\(\\s*['\"]{name}['\"]\\s*\\)"
    return re.search(direct, text) is not None or re.search(call, text) is not None


def _is_import_check(event: dict) -> bool:
    text = event.get("text") or ""
    return any(
        _imports(text, module)
        for module in ("dashboard", "dashboard.backend.server", "installer", "installer.adapters")
    )


def _is_check(event: dict) -> bool:
    if _is_build(event) or _is_wheel_install(event) or event.get("created_venv"):
        return False
    tokens = _tokens(event)
    if _is_orchestra(tokens) or _is_canon(tokens):
        return True
    return _is_import_check(event)


def _pythonpath_has_checkout(event: dict) -> bool:
    for entry in str(event.get("pythonpath") or "").split(os.pathsep):
        if entry and _under_root(entry):
            return True
    return False


def _created_venvs(events: list[dict]) -> list[str]:
    return [event["created_venv"] for event in events if event.get("created_venv")]


def _from_new_venv(event: dict, created: list[str]) -> bool:
    root = event.get("venv_root")
    if not root or not _outside(Path(root)):
        return False
    if _pythonpath_has_checkout(event):
        return False
    resolved = {str(Path(path).resolve()) for path in created}
    return str(Path(root).resolve()) in resolved


def _require(events: list[dict], predicate, label: str) -> dict:
    matches = [event for event in events if predicate(event)]
    assert matches, label
    return matches[0]


def _check_ok(event: dict, created: list[str]) -> None:
    assert event["returncode"] == 0, event.get("stderr") or event.get("argv")
    assert event.get("cwd") and _outside(Path(event["cwd"])), event.get("cwd")
    assert _from_new_venv(event, created), event.get("argv")


def test_wheel_smoke_r5_builds_wheel_when_flag_absent():
    outcome = _default_outcome()
    builds = [event for event in outcome["events"] if _is_uv_build_wheel(event)]
    assert builds, "uv build --wheel was not run\n" + _tail(outcome)
    assert any(event["returncode"] == 0 for event in builds), builds[0].get("stderr")


def test_wheel_smoke_r6_installs_into_new_venv():
    events = _events()
    created = _created_venvs(events)
    assert created, "no new virtual environment was created"
    for path in created:
        assert _outside(Path(path)), path
    installs = [
        event for event in events if _is_wheel_install(event) and event["returncode"] == 0
    ]
    assert installs, "wheel was not installed"
    assert any(_from_new_venv(event, created) for event in installs), installs[0].get("argv")


def test_wheel_smoke_r7_checks_run_outside_checkout():
    events = _events()
    checks = [event for event in events if _is_check(event)]
    assert checks, "no checks were run"
    for event in checks:
        assert event.get("cwd") and _outside(Path(event["cwd"])), event.get("cwd")
        assert not _pythonpath_has_checkout(event), event.get("pythonpath")


def test_wheel_smoke_r8_orchestra_help():
    events = _events()
    created = _created_venvs(events)

    def match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_orchestra(tokens) and "--help" in tokens and "install" not in tokens

    _check_ok(_require(events, match, "orchestra --help did not run"), created)


def test_wheel_smoke_r9_canon_help():
    events = _events()
    created = _created_venvs(events)

    def match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_canon(tokens) and "--help" in tokens

    _check_ok(_require(events, match, "canon --help did not run"), created)


def test_wheel_smoke_r10_canon_init():
    events = _events()
    created = _created_venvs(events)

    def match(event: dict) -> bool:
        tokens = _tokens(event)
        blob = " ".join(tokens)
        return (
            _is_canon(tokens)
            and "init" in tokens
            and "--schemas" in blob
            and "score,conductor,tuner" in blob
        )

    event = _require(events, match, "canon init --schemas score,conductor,tuner did not run")
    _check_ok(event, created)
    assert event.get("is_git"), event.get("cwd")


def test_wheel_smoke_r11_canon_validate():
    events = _events()
    created = _created_venvs(events)

    def init_match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_canon(tokens) and "init" in tokens

    def validate_match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_canon(tokens) and "validate" in tokens and "init" not in tokens

    init_event = _require(events, init_match, "canon init did not run")
    event = _require(events, validate_match, "canon validate did not run")
    _check_ok(event, created)
    assert Path(event["cwd"]).resolve() == Path(init_event["cwd"]).resolve()
    assert event.get("is_git"), event.get("cwd")


def test_wheel_smoke_r12_install_list():
    events = _events()
    created = _created_venvs(events)

    def match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_orchestra(tokens) and "install" in tokens and "--list" in tokens

    _check_ok(_require(events, match, "orchestra install --list did not run"), created)


def test_wheel_smoke_r13_install_list_names_claude():
    events = _events()

    def match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_orchestra(tokens) and "install" in tokens and "--list" in tokens

    event = _require(events, match, "orchestra install --list did not run")
    assert event["returncode"] == 0, event.get("stderr") or event.get("argv")
    assert re.search(r"\bclaude\b", event.get("stdout") or ""), event.get("stdout")


def test_wheel_smoke_r14_import_dashboard():
    _assert_import("dashboard")


def test_wheel_smoke_r15_import_dashboard_web():
    _assert_import("dashboard.backend.server")


def test_wheel_smoke_r16_import_installer():
    _assert_import("installer")


def test_wheel_smoke_r17_import_installer_adapters():
    _assert_import("installer.adapters")


def _assert_import(module: str) -> None:
    events = _events()
    created = _created_venvs(events)
    matches = [
        event
        for event in events
        if _imports(event.get("text") or "", module) and event["returncode"] == 0
    ]
    assert matches, f"new environment did not import {module}"
    _check_ok(matches[0], created)


def test_wheel_smoke_r21_get_root():
    outcome = _default_outcome()
    assert "GET /: pass" in outcome["stdout"].splitlines(), _tail(outcome)


def test_wheel_smoke_r18_wheel_flag_skips_build():
    wheel = _built_wheel()
    outcome = _invoke(["--wheel", str(wheel)])
    assert outcome["returncode"] == 0, _tail(outcome)
    assert not any(_is_build(event) for event in outcome["events"]), "wheel build ran"
    assert any(_installs_wheel(event, wheel) for event in outcome["events"]), "wheel was not installed"


def test_wheel_smoke_r19_missing_providers_json():
    wheel = _built_wheel()
    stripped = _strip_providers(wheel)
    outcome = _invoke(["--wheel", str(stripped)])
    assert outcome["returncode"] != 0, _tail(outcome)


def test_wheel_smoke_r20_checkout_unchanged():
    outcome = _default_outcome()
    assert outcome["before"] == outcome["after"]


def _installs_wheel(event: dict, wheel: Path) -> bool:
    if not _is_wheel_install(event) or event["returncode"] != 0:
        return False
    target = wheel.resolve()
    cwd = Path(event["cwd"])
    for token in _tokens(event):
        if ".whl" not in token:
            continue
        candidate = Path(token)
        if not candidate.is_absolute():
            candidate = cwd / candidate
        try:
            if candidate.resolve() == target and candidate.is_file():
                return True
        except OSError:
            continue
    return False
