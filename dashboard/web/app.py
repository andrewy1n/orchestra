"""FastAPI application factory for the web dashboard launcher.

The launcher (``dashboard/bin/web``) carries its own PEP 723 header with
fastapi and uvicorn; this module only imports them inside :func:`create_app`,
so ``import dashboard.web`` stays usable in environments (like the check
runner) that serve the read API through the standard-library path instead.

The app reads through the same :class:`dashboard.web.service.Reader` the
stdlib server uses and serves the Vite production build from
``dashboard/web/ui/dist`` at ``/`` when it exists.
"""

import inspect
from pathlib import Path

from dashboard import model
from orchestra.canon.project import Project
from dashboard.web.routes import ROUTES
from dashboard.web.service import Reader, WriteError

DIST = Path(__file__).resolve().parent / "ui" / "dist"
MISSING_BUILD = (
    "No web build at dashboard/web/ui/dist. "
    "Run `npm run build` in dashboard/web/ui."
)


def create_app(target: Project):
    """Return a FastAPI app serving the read/write API (and built UI) for ``target``."""
    from fastapi import FastAPI, Query, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="orchestra dashboard")
    reader = Reader(target)

    @app.exception_handler(model.ModelError)
    async def _model_error(_request, exc: model.ModelError) -> JSONResponse:
        return JSONResponse({"error": str(exc)}, status_code=404)

    @app.exception_handler(WriteError)
    async def _write_error(_request, exc: WriteError) -> JSONResponse:
        return JSONResponse({"error": exc.message}, status_code=exc.status)

    def register(route) -> None:
        if route.method == "POST":

            async def write(request: Request) -> dict:
                body = await request.json()
                if not isinstance(body, dict):
                    raise WriteError("JSON body must be an object", 400)
                return getattr(reader, route.reader_method)(body)

            write.__name__ = route.reader_method
            app.add_api_route(route.path, write, methods=[route.method])
            return

        def read(**kwargs: str) -> dict:
            args = [kwargs[key] for key in route.query_keys]
            return getattr(reader, route.reader_method)(*args)

        read.__name__ = route.reader_method
        read.__signature__ = inspect.Signature(
            [
                inspect.Parameter(
                    key,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=Query(...),
                    annotation=str,
                )
                for key in route.query_keys
            ],
            return_annotation=dict,
        )
        app.add_api_route(route.path, read, methods=[route.method])

    for route in ROUTES:
        register(route)

    if DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(DIST), html=True), name="ui")
    else:
        @app.get("/")
        def index() -> HTMLResponse:
            return HTMLResponse(MISSING_BUILD)

    return app
