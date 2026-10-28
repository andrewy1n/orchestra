"""HTTP route parity for the dashboard API.

One store is requested through the stdlib server `dashboard.web.serve` binds
and through ``dashboard.web.app.create_app``. A path listed in
``dashboard.web.routes.ROUTES`` must be dispatched by both.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.web.app import create_app  # noqa: E402
from dashboard.web.routes import ROUTES  # noqa: E402

LISTED = (
    ("GET", "/api/token"),
    ("GET", "/api/snapshot"),
    ("GET", "/api/phase"),
    ("GET", "/api/task"),
    ("GET", "/api/journal"),
    ("GET", "/api/record"),
    ("GET", "/api/requirement"),
    ("GET", "/api/needs"),
    ("GET", "/api/backlog"),
    ("POST", "/api/needs"),
    ("POST", "/api/backlog"),
)

_MISSING_BODIES = (
    {"detail": "Not Found"},
    {"error": "not found"},
)


def _import_web():
    try:
        import dashboard.web as web
        return web
    except ImportError:
        return None


@contextmanager
def _running(store):
    target = open_store(store)
    web = _import_web()
    assert web is not None, "dashboard.web is not importable"
    httpd = None
    try:
        httpd = web.serve(target, host="127.0.0.1", port=0)
    except (FileNotFoundError, AttributeError, TypeError):
        httpd = None
    assert httpd is not None, "dashboard.web.serve(target, host='127.0.0.1', port=0) did not return a server"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _request(method: str, url: str, payload: dict | None = None) -> tuple[int, bytes]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _client(store) -> TestClient:
    target = open_store(store)
    try:
        app = create_app(target)
    except Exception as exc:
        raise AssertionError(f"create_app failed: {exc}") from exc
    return TestClient(app, raise_server_exceptions=False)


def _query(route) -> dict[str, str]:
    return {key: "parity" for key in route.query_keys}


def _unregistered(status: int, payload: dict) -> bool:
    if status == 405:
        return True
    return status == 404 and payload in _MISSING_BODIES


def _stdlib(base: str, route) -> tuple[int, dict]:
    query = urllib.parse.urlencode(_query(route))
    url = base + route.path
    if query:
        url = f"{url}?{query}"
    payload = {} if route.method == "POST" else None
    status, body = _request(route.method, url, payload)
    parsed = json.loads(body)
    assert isinstance(parsed, dict), (route.method, route.path, parsed)
    return status, parsed


def _fastapi(client: TestClient, route) -> tuple[int, dict]:
    if route.method == "POST":
        response = client.post(route.path, json={})
    else:
        response = client.get(route.path, params=_query(route))
    parsed = response.json()
    assert isinstance(parsed, dict), (route.method, route.path, parsed)
    return response.status_code, parsed


def test_route_parity(store):
    """Each listed API path is dispatched by the stdlib server and the FastAPI app."""
    routes = {(route.method, route.path): route for route in ROUTES}
    assert set(routes) == set(LISTED)
    with _running(store) as base:
        client = _client(store)
        for method, path in LISTED:
            route = routes[(method, path)]
            stdlib_status, stdlib_body = _stdlib(base, route)
            fastapi_status, fastapi_body = _fastapi(client, route)
            label = f"{method} {path}"
            assert not _unregistered(stdlib_status, stdlib_body), (
                label, "stdlib", stdlib_status, stdlib_body,
            )
            assert not _unregistered(fastapi_status, fastapi_body), (
                label, "fastapi", fastapi_status, fastapi_body,
            )
            assert stdlib_status == fastapi_status, (
                label, stdlib_status, fastapi_status, stdlib_body, fastapi_body,
            )
            if "error" in stdlib_body or "error" in fastapi_body:
                assert stdlib_body.get("error") == fastapi_body.get("error"), (
                    label, stdlib_body, fastapi_body,
                )
