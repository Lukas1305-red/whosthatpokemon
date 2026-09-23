.PHONY: install fetch enrich populate pipeline lint python-lint client-lint test evaluate server client dev docker

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
	python-lint client-lint

python-lint:
	uv run pre-commit run ruff-check --all-files
	uv run pre-commit run ruff-format --all-files

client-lint:
	cd client && bun run lint

test:
	PYTHONPATH=. uv run python -m pytest -s

evaluate:
	PYTHONPATH=. uv run python evaluation/run_$(EVAL_SUITE).py $(EVAL_ARGS)

server:
	uv run uvicorn server.main:app --reload

docker:
	docker compose up --build

client:
	cd client && bun dev

dev:
	@trap 'kill 0' INT TERM EXIT; \
  $(MAKE) server & \
  $(MAKE) client & \
  wait
