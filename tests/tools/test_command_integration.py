from __future__ import annotations

from pathlib import Path

from orchestra.tools import Command, SshKeygen


def test_real_sh_line(tmp_path: Path) -> None:
    result = Command().shell("echo out; echo err >&2; exit 3", cwd=tmp_path)

    assert result.returncode == 3
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"
    assert not result.timed_out
    assert not result.missing


def test_real_ssh_keygen_round_trip(tmp_path: Path) -> None:
    generated = Command().run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", "key"], cwd=tmp_path)
    assert generated.returncode == 0

    public_key = (tmp_path / "key.pub").read_text().strip()
    allowlist = tmp_path / "allowed_signers"
    allowlist.write_text(f'principal namespaces="ns" {public_key}\n')

    ssh = SshKeygen(tmp_path)
    payload = b"payload bytes\n"
    signature = tmp_path / "payload.sig"
    signature.write_text(ssh.sign("ns", payload, tmp_path / "key"))

    assert ssh.verify(allowlist, "principal", "ns", signature, payload) is True
    assert ssh.verify(allowlist, "principal", "ns", signature, b"tampered\n") is False
