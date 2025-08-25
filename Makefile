.PHONY: test

test:
    uv run pytest -v --disable-warnings --maxfail=1

build:
	uv build

testcoverage:
	uv run pytest --cov=src --cov-report=xml --disable-warnings --maxfail=1