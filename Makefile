.PHONY: install fetch enrich populate pipeline lint server

install:
	uv sync

fetch:
	PYTHONPATH=. uv run python scripts/fetch_pokemon.py

enrich:
	PYTHONPATH=. uv run python scripts/enrich_pokemon.py

populate:
	PYTHONPATH=. uv run python scripts/populate_db.py

pipeline: fetch enrich populate

lint:
	uv run pre-commit run --all-files

test:
	PYTHONPATH=. uv run python -m pytest -s

server:
	uv run uvicorn server.main:app --reload