"""In-process read/write API for the web dashboard.

``serve(target, host, port)`` returns a standard-library ``ThreadingHTTPServer``
the tests can drive directly; the FastAPI application the launcher
runs is ``create_app(target)``. Both build their payloads from
``dashboard.model`` through :mod:`dashboard.web.service`.
"""

from __future__ import annotations

from dashboard.web.app import create_app
from dashboard.web.service import Cache, Reader, WriteError, serve

__all__ = ["Cache", "Reader", "WriteError", "create_app", "serve"]
