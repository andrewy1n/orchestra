from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from orchestra.tools import SshKeygen, ToolError


class FakeRun:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.calls: list[tuple[list[str], bytes | str | None]] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[True],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]: ...

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[False],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[bytes]: ...

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        self.calls.append((list(argv), input))
        assert not text
        return subprocess.CompletedProcess(list(argv), self.returncode, self.stdout, self.stderr)


def test_ssh_keygen_has_no_version_check(tmp_path: Path) -> None:
    run = FakeRun(stdout=b"sig")
    tool = SshKeygen(tmp_path, run=run)
    assert tool.version_args is None
    tool.sign("ns", b"data", tmp_path / "key")
    assert [argv[1] for argv, _ in run.calls] == ["-Y"]


def test_sign_returns_signature_text(tmp_path: Path) -> None:
    run = FakeRun(stdout=b"-----BEGIN SSH SIGNATURE-----\n")
    tool = SshKeygen(tmp_path, run=run)
    assert tool.sign("ns", b"data", tmp_path / "key") == "-----BEGIN SSH SIGNATURE-----\n"
    assert run.calls == [
        (["ssh-keygen", "-Y", "sign", "-f", str(tmp_path / "key"), "-n", "ns"], b"data")
    ]


@pytest.mark.parametrize(("returncode", "expected"), [(0, True), (255, False)])
def test_verify_returns_match(tmp_path: Path, returncode: int, expected: bool) -> None:
    run = FakeRun(returncode=returncode, stderr=b"no")
    tool = SshKeygen(tmp_path, run=run)
    allowlist, signature = tmp_path / "allowed", tmp_path / "x.sig"
    assert tool.verify(allowlist, "me", "ns", signature, b"data") is expected
    assert run.calls == [
        (
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowlist),
                "-I",
                "me",
                "-n",
                "ns",
                "-s",
                str(signature),
            ],
            b"data",
        )
    ]


def test_sign_raises_tool_error_on_failure(tmp_path: Path) -> None:
    tool = SshKeygen(tmp_path, run=FakeRun(returncode=1, stderr=b"bad key"))
    with pytest.raises(ToolError) as info:
        tool.sign("ns", b"data", tmp_path / "key")
    assert info.value.returncode == 1
    assert "bad key" in info.value.stderr
