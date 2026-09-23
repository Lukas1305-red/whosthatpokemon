.PHONY: install fetch enrich populate pipeline lint test evaluate server docker

EVAL_SUITE ?= retrieval

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

evaluate:
	PYTHONPATH=. uv run python evaluation/run_$(EVAL_SUITE).py $(EVAL_ARGS)

server:
	uv run uvicorn server.main:app --reload

docker:
	docker compose up --build
