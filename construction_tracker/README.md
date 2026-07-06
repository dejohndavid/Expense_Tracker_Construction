# Finance Engine

Finance Engine is a personal construction expense tracker. It imports HDFC bank statement exports, classifies construction-related transactions using a keyword rule engine, lets you review and correct matches, and persists the results to a local SQLite database with spend reports.

## Architecture

```
HDFC Text Export → Parser → Review Queue ← Rule Engine
                                ↓
                         SQLite Database
                                ↓
                    Reports & Ledger Exports
```

```
backend/
  config/       Pydantic settings (.env backed)
  core/         Logging setup (Loguru)
  db/           SQLAlchemy models, session, Base
  modules/
    imports/    HDFC parser + review row builder
    vendors/    Rule engine + DB-backed rule loader
    transactions/ Persistence service
    reports/    Spend aggregation service
  routers/      FastAPI routers (transactions, rules, reports)
  main.py       FastAPI app entrypoint
frontend/
  streamlit/    Single-page import review UI
alembic/        DB migrations
tests/          pytest suite
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — the package manager used by this project

Install uv (if you don't have it):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

```bash
# Clone and enter the project directory
cd construction_tracker

# Install all dependencies into an isolated virtual environment
uv sync
```

That's it. The SQLite database (`finance.db`) and default classification rules are created automatically on first startup — no manual database setup needed.

If you want to override any default settings, copy the example env file:
```bash
cp .env.example .env
# Edit .env as needed
```

## Running

```bash
# Start the FastAPI backend (http://localhost:8000)
make api

# Start the Streamlit UI (http://localhost:8501)
make ui
```

Both commands must be run from the `construction_tracker/` directory.

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) once the backend is running.

## Workflow

1. Export your HDFC statement as a `.txt` file from HDFC NetBanking.
2. Open the Streamlit UI (`make ui`) and upload the file.
3. The parser classifies each debit as **Ready**, **Needs Review**, or **Ignored**.
4. Edit any misclassified rows in the review table.
5. Click **Save to database** to persist the reviewed transactions.
6. Switch to the **Reports** tab to see spend breakdowns by category and construction stage.
7. Download a full reviewed CSV or a ready-only ledger CSV from the **Ready Ledger** tab.

## Database migrations

Migrations are managed with Alembic. The initial schema is applied automatically on startup via `create_all_tables()`.

For subsequent schema changes:
```bash
# Apply all pending migrations
make db-upgrade

# Generate a new migration after changing models
make db-revision msg="add project column to transactions"

# Roll back the last migration
make db-downgrade
```

## Development

```bash
# Run the full test suite
make test

# Lint and type-check
make lint

# Auto-format
make format

# Remove all cache directories
make clean
```

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | uv |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Database | SQLite via SQLAlchemy + Alembic |
| Settings | Pydantic-Settings |
| Logging | Loguru |
| Linting | Ruff + Black |
| Type checking | mypy (strict) |
| Testing | pytest |

## Roadmap

- PR-001 Bootstrap project — done
- PR-002 HDFC text parser — done
- PR-003 Transaction import engine — done
- PR-004 Vendor and rule matching engine — done
- PR-005 Review workflow + DB persistence — done
- PR-006 Reports and dashboards — done
- PR-007 Excel export — pending
