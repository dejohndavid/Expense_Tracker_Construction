from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from backend.config.settings import get_settings
from backend.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from backend.db.session import create_all_tables, get_db
    from backend.modules.vendors.rule_loader import seed_default_rules

    create_all_tables()
    db_gen = get_db()
    db = next(db_gen)
    try:
        seed_default_rules(db)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

from backend.routers import reports, rules, transactions  # noqa: E402

app.include_router(transactions.router)
app.include_router(rules.router)
app.include_router(reports.router)


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
