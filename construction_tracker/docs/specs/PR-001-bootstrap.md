# PR-001 - Project Bootstrap

## Title

Bootstrap the Finance Engine project with a production-ready development environment.

## Goal

Create the initial project structure, development tooling, and application bootstrap for the Finance Engine.

This PR must not implement business logic:

- No HDFC parsing
- No database models
- No transaction processing
- No vendor matching

The objective is to establish a clean, maintainable foundation that future work can build on.

## Architecture

- Backend: FastAPI
- Frontend: Streamlit
- Database: SQLite placeholder
- Package manager: uv
- Language: Python 3.12+
- Architecture style: vertical slice modules

## Repository Structure

```text
backend/
  main.py
  config/settings.py
  core/logging.py
  modules/
    transactions/
    vendors/
    imports/
    reports/
    projects/
frontend/streamlit/app.py
docs/specs/PR-001-bootstrap.md
tests/
.github/workflows/ci.yml
.env.example
.gitignore
.pre-commit-config.yaml
Makefile
pyproject.toml
README.md
```

## Acceptance Criteria

- `uv sync` installs dependencies.
- `make api` starts FastAPI.
- `make ui` starts Streamlit.
- `make lint` runs Ruff, Black, and MyPy.
- `make test` runs the test suite.
- GitHub Actions runs lint and tests.
- No business logic is included.

## Out Of Scope

- SQLAlchemy models
- Alembic migrations
- HDFC parser
- Import engine
- Vendor/rule matching
- Dashboard reports
- Excel exports
- Authentication

## Definition Of Done

- Project builds successfully.
- FastAPI app exposes `/` and `/health`.
- Streamlit app launches.
- Settings load from environment variables.
- Logging is configured.
- Tests cover the bootstrap endpoints.
