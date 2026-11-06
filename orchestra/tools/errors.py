from __future__ import annotations

from collections.abc import Sequence


class ToolError(RuntimeError):
    def __init__(
        self,
        message: str,
        argv: Sequence[str],
        returncode: int | None,
        stderr: str,
    ) -> None:
        super().__init__(message)
        self.argv: tuple[str, ...] = tuple(argv)
        self.returncode: int | None = returncode
        self.stderr: str = stderr


class ToolVersionError(ToolError):
    pass


class ToolNotFoundError(ToolError):
    pass
