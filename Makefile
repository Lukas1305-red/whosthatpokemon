.PHONY: install fetch enrich lint

install:
	uv sync

fetch:
	PYTHONPATH=. uv run python scripts/fetch_pokemon.py

enrich:
	PYTHONPATH=. uv run python scripts/enrich_pokemon.py

lint:
	uv run pre-commit run --all-files