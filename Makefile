.PHONY: install fetch

install:
	uv sync

fetch:
	uv run python scripts/fetch_pokemon.py

lint:
	uv run pre-commit run --all-files