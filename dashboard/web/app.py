"""FastAPI application factory for the web dashboard launcher.

The launcher (``dashboard/bin/web``) carries its own PEP 723 header with
fastapi and uvicorn; this module only imports them inside :func:`create_app`,
so ``import dashboard.web`` stays usable in environments (like the check
runner) that serve the read API through the standard-library path instead.

The app reads through the same :class:`dashboard.web.service.Reader` the
stdlib server uses and serves the Vite production build from
``dashboard/web/ui/dist`` at ``/`` when it exists.
"""

from __future__ import annotations

from pathlib import Path

from dashboard import model
from dashboard.artifact_store import Target
from dashboard.web.service import Reader

DIST = Path(__file__).resolve().parent / "ui" / "dist"
MISSING_BUILD = (
    "No web build at dashboard/web/ui/dist. "
    "Run `npm run build` in dashboard/web/ui."
)


def create_app(target: Target):
    """Return a FastAPI app serving the read API (and built UI) for ``target``."""
    from fastapi import FastAPI, Query
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="orchestra dashboard")
    reader = Reader(target)

    @app.exception_handler(model.ModelError)
    async def _model_error(_request, exc: model.ModelError) -> JSONResponse:
        return JSONResponse({"error": str(exc)}, status_code=404)

    @app.get("/api/token")
    def token() -> dict:
        return reader.token()

    @app.get("/api/snapshot")
    def snapshot() -> dict:
        return reader.snapshot()

    @app.get("/api/phase")
    def phase(effort: str = Query(...), phase: str = Query(...)) -> dict:
        return reader.phase(effort, phase)

    @app.get("/api/task")
    def task(id: str = Query(...)) -> dict:
        return reader.task(id)

    @app.get("/api/journal")
    def journal(effort: str = Query(...)) -> dict:
        return reader.journal(effort)

    @app.get("/api/record")
    def record(id: str = Query(...)) -> dict:
        return reader.record(id)

    @app.get("/api/requirement")
    def requirement(effort: str = Query(...), phase: str = Query(...), id: str = Query(...)) -> dict:
        return reader.requirement(effort, phase, id)

    @app.get("/api/needs")
    def needs(effort: str = Query(...), id: str = Query(...)) -> dict:
        return reader.needs(effort, id)

    @app.get("/api/backlog")
    def backlog(effort: str = Query(...), id: str = Query(...)) -> dict:
        return reader.backlog(effort, id)

    if DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(DIST), html=True), name="ui")
    else:
        @app.get("/")
        def index() -> HTMLResponse:
            return HTMLResponse(MISSING_BUILD)

    return app
