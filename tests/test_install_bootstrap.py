"""Oracle tests for the root install.sh bootstrap."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"
GIT_FROM = "git+https://github.com/andrewy1n/orchestra@"
UV_INSTALLER = "https://astral.sh/uv/install.sh"
_TIMEOUT_SECONDS = 15

_FAKE_TOOL = """\
#!PYTHON
import os
import sys
from pathlib import Path


def _stdin_source() -> str:
    if os.isatty(0):
        return "tty"
    return os.readlink("/proc/self/fd/0")


def _log_call() -> None:
    tool = Path(sys.argv[0]).name
    fields = [tool, _stdin_source(), *sys.argv[1:]]
    log = Path(os.environ["INSTALL_BOOTSTRAP_LOG"])
    with log.open("a", encoding="utf-8") as handle:
        handle.write("\\t".join(fields) + "\\n")


def _install_uv_stub() -> None:
    if "UV_INSTALLER_URL" not in sys.argv[1:]:
        return
    destination = Path(os.environ["HOME"]) / ".local" / "bin" / "uv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = Path(os.environ["INSTALL_BOOTSTRAP_FAKE"])
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    destination.chmod(0o755)


def _print_uname() -> None:
    args = sys.argv[1:]
    if "-m" in args and "-s" not in args:
        sys.stdout.write("x86_64\\n")
        return
    sys.stdout.write(os.environ["INSTALL_BOOTSTRAP_UNAME"] + "\\n")


def main() -> None:
    tool = Path(sys.argv[0]).name
    _log_call()
    if tool == "uname":
        _print_uname()
        return
    if tool == "curl":
        _install_uv_stub()


if __name__ == "__main__":
    main()
"""

_TTY_RUNNER = """\
import fcntl
import os
import pty
import sys
import termios


def _adopt_tty() -> None:
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    reader = os.fork()
    if reader == 0:
        os.close(slave)
        while True:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                os._exit(0)
            if not chunk:
                os._exit(0)
    os.close(master)
    os.set_inheritable(slave, True)


def main() -> None:
    mode = sys.argv[1]
    script = sys.argv[2]
    args = sys.argv[3:]
    if mode == "tty":
        _adopt_tty()
    os.execvpe("sh", ["sh", script, *args], os.environ)


if __name__ == "__main__":
    main()
"""


@dataclass(frozen=True)
class Call:
    tool: str
    argv: tuple[str, ...]
    stdin: str


@dataclass(frozen=True)
class Outcome:
    calls: tuple[Call, ...]
    returncode: int
    stdout: str
    stderr: str


def _fake_tool_text() -> str:
    return _FAKE_TOOL.replace("#!PYTHON", f"#!{sys.executable}", 1).replace(
        "UV_INSTALLER_URL", UV_INSTALLER, 1
    )


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _calls(log: Path) -> tuple[Call, ...]:
    found: list[Call] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        tool, stdin, *argv = line.split("\t")
        found.append(Call(tool, tuple(argv), stdin))
    return tuple(found)


def _install_argv(
    ref: str, forwarded: tuple[str, ...] = (), *, add_yes: bool = False
) -> tuple[str, ...]:
    install_args = (*forwarded, "--yes") if add_yes else forwarded
    return ("--from", f"{GIT_FROM}{ref}", "orchestra", "install", *install_args)


def _install_calls(calls: tuple[Call, ...]) -> tuple[Call, ...]:
    selected: list[Call] = []
    for call in calls:
        if call.tool != "uvx":
            continue
        argv = call.argv
        if len(argv) < 4 or argv[0] != "--from" or argv[2] != "orchestra" or argv[3] != "install":
            continue
        selected.append(call)
    return tuple(selected)


def _execute(
    tmp: Path,
    args: tuple[str, ...],
    *,
    ref: str | None,
    uv: bool,
    uname: str,
    tty: bool,
) -> Outcome:
    bin_dir = tmp / "bin"
    home = tmp / "home"
    bin_dir.mkdir()
    (home / ".local" / "bin").mkdir(parents=True)
    (tmp / "tmp").mkdir()
    log = tmp / "calls.log"
    log.write_text("", encoding="utf-8")
    fake = _fake_tool_text()
    names = ["uvx", "curl", "uname"]
    if uv:
        names.append("uv")
    for name in names:
        _write_executable(bin_dir / name, fake)
    runner = tmp / "tty-runner.py"
    runner.write_text(_TTY_RUNNER, encoding="utf-8")
    env = {
        "PATH": os.pathsep.join((str(bin_dir), str(home / ".local" / "bin"), "/usr/bin", "/bin")),
        "HOME": str(home),
        "TMPDIR": str(tmp / "tmp"),
        "INSTALL_BOOTSTRAP_LOG": str(log),
        "INSTALL_BOOTSTRAP_FAKE": str(bin_dir / "uvx"),
        "INSTALL_BOOTSTRAP_UNAME": uname,
        "LANG": "C",
        "LC_ALL": "C",
    }
    if ref is not None:
        env["ORCHESTRA_REF"] = ref
    completed = subprocess.run(
        [sys.executable, str(runner), "tty" if tty else "plain", str(INSTALL_SH), *args],
        cwd=tmp,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        start_new_session=True,
        check=False,
    )
    return Outcome(_calls(log), completed.returncode, completed.stdout, completed.stderr)


def _assert_printed(outcome: Outcome) -> None:
    assert outcome.returncode == 0
    assert outcome.stdout.strip() != ""


def test_runs_uvx_from_ref(tmp_path: Path) -> None:
    """R1: install.sh runs `orchestra install` through uvx from the git ref."""
    ref = "ref-r1"
    expected = [_install_argv(ref)]
    for uname in ("Linux", "Darwin"):
        work = tmp_path / uname
        work.mkdir()
        outcome = _execute(work, (), ref=ref, uv=True, uname=uname, tty=True)
        assert [call.argv for call in _install_calls(outcome.calls)] == expected
        assert not any(call.tool == "curl" and UV_INSTALLER in call.argv for call in outcome.calls)
        _assert_printed(outcome)


def test_installs_uv_when_missing(tmp_path: Path) -> None:
    """R2: install.sh installs uv first when uv is missing."""
    outcome = _execute(tmp_path, (), ref="main", uv=False, uname="Linux", tty=True)
    trace = tuple(
        call.tool
        for call in outcome.calls
        if (call.tool == "curl" and UV_INSTALLER in call.argv) or call.tool == "uvx"
    )
    assert trace == ("curl", "uvx")
    assert [call.argv for call in _install_calls(outcome.calls)] == [_install_argv("main")]
    _assert_printed(outcome)


def test_reads_orchestra_ref(tmp_path: Path) -> None:
    """R3: install.sh reads the git ref from ORCHESTRA_REF."""
    ref = "ref-r3"
    outcome = _execute(tmp_path, (), ref=ref, uv=True, uname="Linux", tty=True)
    assert [call.argv for call in _install_calls(outcome.calls)] == [_install_argv(ref)]
    _assert_printed(outcome)


def test_defaults_ref_to_main(tmp_path: Path) -> None:
    """R4: install.sh uses main when ORCHESTRA_REF is unset."""
    outcome = _execute(tmp_path, (), ref=None, uv=True, uname="Linux", tty=True)
    assert [call.argv for call in _install_calls(outcome.calls)] == [_install_argv("main")]
    _assert_printed(outcome)


def test_forwards_arguments(tmp_path: Path) -> None:
    """R5: install.sh passes its arguments to `orchestra install`."""
    forwarded = ("--scope", "project", "--copy")
    outcome = _execute(tmp_path, forwarded, ref="ref-r5", uv=True, uname="Linux", tty=True)
    assert [call.argv for call in _install_calls(outcome.calls)] == [
        _install_argv("ref-r5", forwarded)
    ]
    _assert_printed(outcome)


def test_reattaches_tty(tmp_path: Path) -> None:
    """R6: When /dev/tty is readable, install.sh runs `orchestra install` with stdin from /dev/tty."""
    ref = "ref-r6"
    outcome = _execute(tmp_path, (), ref=ref, uv=True, uname="Linux", tty=True)
    observed = [(call.argv, call.stdin) for call in _install_calls(outcome.calls)]
    assert observed == [(_install_argv(ref), "tty")]
    _assert_printed(outcome)


def test_adds_yes_without_tty(tmp_path: Path) -> None:
    """R7: When /dev/tty is not readable, install.sh adds --yes."""
    outcome = _execute(tmp_path, (), ref="main", uv=True, uname="Linux", tty=False)
    observed = [(call.argv, call.stdin) for call in _install_calls(outcome.calls)]
    assert observed == [(_install_argv("main", add_yes=True), "/dev/null")]
    _assert_printed(outcome)


def test_rejects_unsupported_os(tmp_path: Path) -> None:
    """R8: install.sh exits non-zero with a message on an unsupported OS."""
    outcome = _execute(tmp_path, (), ref="main", uv=True, uname="FreeBSD", tty=False)
    message = f"{outcome.stdout}{outcome.stderr}".lower()
    assert outcome.returncode != 0 and "freebsd" in message and "support" in message
