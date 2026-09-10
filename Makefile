.PHONY: install fetch summarize lint

install:
	uv sync

fetch:
	PYTHONPATH=. uv run python scripts/fetch_pokemon.py

summarize:
	PYTHONPATH=. uv run python scripts/summarize_flavour_texts.py

lint:
	uv run pre-commit run --all-files