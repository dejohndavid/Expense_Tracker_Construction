from fastapi import FastAPI

from backend.config.settings import get_settings
from backend.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
    }


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}
