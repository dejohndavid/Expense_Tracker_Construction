.PHONY: api ui lint format test db-upgrade db-downgrade db-revision clean

api:
	uv run uvicorn backend.main:app --reload

ui:
	PYTHONPATH=. uv run streamlit run frontend/streamlit/app.py

lint:
	uv run ruff check .
	uv run black --check .
	uv run mypy backend frontend tests

format:
	uv run ruff check . --fix
	uv run black .

test:
	uv run pytest

db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

db-revision:
	uv run alembic revision --autogenerate -m "$(msg)"

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
