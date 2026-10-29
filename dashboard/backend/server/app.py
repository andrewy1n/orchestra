"""FastAPI application factory for the web dashboard launcher.

Serves the Vite production build from ``dashboard/web/ui/dist`` at ``/``
when it exists.
"""

from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from dashboard.backend import store
from dashboard.backend.server import schemas
from dashboard.backend.server.service import Reader, WriteError
from orchestra.canon.project import Project

DIST = Path(__file__).resolve().parent.parent.parent / "web" / "ui" / "dist"
MISSING_BUILD = (
    "No web build at dashboard/web/ui/dist. "
    "Run `npm run build` in dashboard/web/ui."
)


ERRORS: dict[int | str, dict] = {400: {"model": schemas.ErrorBody}, 404: {"model": schemas.ErrorBody}, 409: {"model": schemas.ErrorBody}}


def create_app(target: Project):
    """Return a FastAPI app serving the read/write API (and built UI) for ``target``."""
    app = FastAPI(title="orchestra dashboard")
    reader = Reader(target)

    @app.exception_handler(store.ModelError)
    async def _model_error(_request, exc: store.ModelError) -> JSONResponse:
        return JSONResponse({"error": str(exc)}, status_code=404)

    @app.exception_handler(WriteError)
    async def _write_error(_request, exc: WriteError) -> JSONResponse:
        return JSONResponse({"error": exc.message}, status_code=exc.status)

    @app.get("/api/token", response_model=schemas.TokenResponse, responses=ERRORS)
    def token() -> schemas.TokenResponse:
        return reader.token()

    @app.get("/api/snapshot", response_model=schemas.SnapshotResponse, responses=ERRORS)
    def snapshot() -> schemas.SnapshotResponse:
        return reader.snapshot()

    @app.get("/api/phase", response_model=schemas.PhaseResponse, responses=ERRORS)
    def phase(effort: str = Query(...), phase: str = Query(...)) -> schemas.PhaseResponse:
        return reader.phase(effort, phase)

    @app.get("/api/task", response_model=schemas.TaskResponse, responses=ERRORS)
    def task(id: str = Query(...)) -> schemas.TaskResponse:
        return reader.task(id)

    @app.get("/api/journal", response_model=schemas.JournalResponse, responses=ERRORS)
    def journal(effort: str = Query(...)) -> schemas.JournalResponse:
        return reader.journal(effort)

    @app.get("/api/record", response_model=schemas.RecordResponse, responses=ERRORS)
    def record(id: str = Query(...)) -> schemas.RecordResponse:
        return reader.record(id)

    @app.get("/api/requirement", response_model=schemas.RequirementResponse, responses=ERRORS)
    def requirement(effort: str = Query(...), phase: str = Query(...), id: str = Query(...)) -> schemas.RequirementResponse:
        return reader.requirement(effort, phase, id)

    @app.get("/api/needs", response_model=schemas.NeedsResponse, responses=ERRORS)
    def needs(effort: str = Query(...), id: str = Query(...)) -> schemas.NeedsResponse:
        return reader.needs(effort, id)

    @app.get("/api/backlog", response_model=schemas.BacklogResponse, responses=ERRORS)
    def backlog(effort: str = Query(...), id: str = Query(...)) -> schemas.BacklogResponse:
        return reader.backlog(effort, id)

    @app.post("/api/needs", response_model=schemas.OkResponse, responses=ERRORS)
    async def write_needs(request: Request) -> schemas.OkResponse:
        body = await request.json()
        if not isinstance(body, dict):
            raise WriteError("JSON body must be an object", 400)
        return reader.write_needs(body)

    @app.post("/api/backlog", response_model=schemas.OkResponse, responses=ERRORS)
    async def write_backlog(request: Request) -> schemas.OkResponse:
        body = await request.json()
        if not isinstance(body, dict):
            raise WriteError("JSON body must be an object", 400)
        return reader.write_backlog(body)

    if DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(DIST), html=True), name="ui")
    else:
        @app.get("/", include_in_schema=False)
        def index() -> HTMLResponse:
            return HTMLResponse(MISSING_BUILD)

    return app
