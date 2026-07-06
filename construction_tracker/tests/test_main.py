from starlette.routing import Route

from backend.main import app, read_health, read_root


def test_root_endpoint() -> None:
    assert read_root() == {
        "application": "Finance Engine",
        "version": "0.1.0",
        "status": "healthy",
    }


def test_health_endpoint() -> None:
    assert read_health() == {"status": "ok"}


def test_fastapi_routes_are_registered() -> None:
    paths = {route.path for route in app.routes if isinstance(route, Route)}
    assert "/" in paths
    assert "/health" in paths
