from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from orchestra.tools.cli_tool import CliTool


class SshKeygen(CliTool):
    executable: ClassVar[str] = "ssh-keygen"
    version_args: ClassVar[Sequence[str] | None] = None

    def sign(self, namespace: str, payload: bytes, key_path: Path) -> str:
        result = self._execute_bytes(["-Y", "sign", "-f", str(key_path), "-n", namespace], payload)
        return result.stdout.decode("utf-8")

    def verify(
        self,
        allowlist: Path,
        principal: str,
        namespace: str,
        signature: Path,
        payload: bytes,
    ) -> bool:
        result = self._run_bytes(
            [
                "-Y",
                "verify",
                "-f",
                str(allowlist),
                "-I",
                principal,
                "-n",
                namespace,
                "-s",
                str(signature),
            ],
            payload,
        )
        return result.returncode == 0
