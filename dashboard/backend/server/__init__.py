"""In-process read/write API for the web dashboard.

``serve(target, host, port)`` returns a standard-library ``ThreadingHTTPServer``
the tests can drive directly; the FastAPI application the launcher
runs is ``create_app(target)``. Both build their payloads from
``dashboard.backend.model`` through :mod:`dashboard.backend.server.service`.
"""

from __future__ import annotations

from dashboard.backend.server.app import create_app
from dashboard.backend.server.service import Cache, Reader, WriteError, serve

__all__ = ["Cache", "Reader", "WriteError", "create_app", "serve"]
