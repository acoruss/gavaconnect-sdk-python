.PHONY: test build testcoverage dev-build ruff-check ruff-format mypy bandit

test:
	uv run pytest -v --disable-warnings --maxfail=1

test-coverage:
	uv run pytest --cov=src --cov-report=xml --disable-warnings --maxfail=1

build:
	uv build

dev-build:
	uv build --wheel

ruff-check:
	uv run ruff check .

ruff-format:
	uv run ruff format .

mypy:
	uv run mypy .

bandit:
	uv run bandit -r src/