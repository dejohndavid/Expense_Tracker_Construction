.PHONY: api ui lint format test clean

api:
	uv run uvicorn backend.main:app --reload

ui:
	uv run streamlit run frontend/streamlit/app.py

lint:
	uv run ruff check .
	uv run black --check .
	uv run mypy backend frontend tests

format:
	uv run ruff check . --fix
	uv run black .

test:
	uv run pytest

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
