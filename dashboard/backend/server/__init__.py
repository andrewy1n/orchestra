"""FastAPI read/write API for the web dashboard.

``create_app(target)`` returns the application the launcher runs.
"""

from __future__ import annotations

from dashboard.backend.server.app import create_app
from dashboard.backend.server.service import Cache, Reader, WriteError

__all__ = ["Cache", "Reader", "WriteError", "create_app"]
