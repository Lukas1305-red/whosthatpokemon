# Who's That Pokémon?

![image](assets/SystemDesign_Pokemon.png)

An API that recommends Pokémon based on personal traits. Send qualities such as
`calm`, `protective`, or `curious`; the service searches a semantically enriched
Pokémon collection and can explain why a chosen result is a good fit.

The project is a Python 3.13 / FastAPI backend. It uses Cohere for embeddings
and default reranking, Chroma for vector search, Anthropic for optional
explanations, and Redis for shared cache and daily LLM-spend protection.

## What happens in a request

```text
POST /search
  → query builder → Cohere embedding → Chroma candidate search
  → Cohere rerank (top 25 candidates → top 5 results)

POST /explain
  → explanation cache → daily LLM budget → Anthropic (on a cache miss)
```

Reranking is the standard search path. If Cohere reranking is temporarily
rate-limited or has a retryable failure, the API returns the original vector
ranking and reports that in the response metadata.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Cohere and Anthropic API keys
- Docker Desktop, if you want to use the Compose deployment

## Get started locally

1. Install dependencies and create your local environment file.

   ```sh
   make install
   cp .env.example .env
   ```

2. Add your provider credentials to `.env`.

   ```dotenv
   ANTHROPIC_API_KEY=your-key
   COHERE_API_KEY=your-key
   ```

3. Build the local Chroma index. This fetches Pokémon source data, enriches it,
   and creates embeddings, so it requires your provider credentials and may
   incur API usage.

   ```sh
   make pipeline
   ```

4. Start the API.

   ```sh
   make server
   ```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive
API documentation. Use `http://localhost:8000/health` to confirm that the
server is running.

## Try the API

Search for suitable Pokémon:

```sh
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "traits": ["calm", "protective"],
    "note": "For a quiet home."
  }'
```

Use an ID from the search response to request an explanation:

```sh
curl -X POST http://localhost:8000/explain \
  -H 'Content-Type: application/json' \
  -d '{
    "searchRequest": {
      "traits": ["calm", "protective"],
      "note": "For a quiet home."
    },
    "pokemon_id": "131"
  }'
```

Valid traits are `reliable`, `independent`, `calm`, `curious`, `protective`,
and `adaptable`. An explanation cache hit returns immediately without consuming
daily LLM budget or calling Anthropic.

## Run with Docker

Docker Compose starts the API and Redis. It mounts your local `data/` directory,
which must contain the generated Chroma index.

```sh
cp .env.example .env
# Add ANTHROPIC_API_KEY and COHERE_API_KEY to .env.
docker compose up --build
```

The API is then available at `http://localhost:8000`. In this mode Redis stores
the daily explanation budget and shared, TTL-based explanation responses.

## Configuration

Copy `.env.example` and adjust values for your environment. The most useful
settings are:

- `ANTHROPIC_API_KEY`, `COHERE_API_KEY`: required provider credentials.
- `TRUSTED_HOSTS`: comma-separated allowed request hosts. Local defaults are
  `localhost,127.0.0.1`.
- `ALLOWED_ORIGINS`: comma-separated browser origins allowed by CORS.
- `LLM_ENABLED`: set to `false` to disable paid explanation generation while
  keeping search available.
- `EXPLAIN_DAILY_LLM_BUDGET`: maximum number of cache-miss explanations per
  UTC day.
- `EXPLAIN_CACHE_TTL_SECONDS`: explanation-cache lifetime; defaults to one day.
- `REDIS_URL`: enables Redis-backed cache and budget storage outside Compose.

For a public deployment, set explicit hosts and origins, terminate HTTPS at the
edge, persist `data/chroma`, and use a managed Redis service. The embedded
Chroma index is intended for a single API instance; move it to a server-backed
vector store before adding replicas.

## Project layout

```text
server/
  api/            FastAPI routes, schemas, dependency wiring, and rate limits
  services/       Query building, search orchestration, caching, LLM budget
  repositories/   Chroma and Redis access
scripts/          Data fetch, enrichment, and Chroma-index generation
evaluation/       Retrieval evaluation suite and methodology
tests/            API, service, cache, budget, and deployment tests
```

## Development commands

```sh
make test                         # Run the test suite
make lint                         # Run pre-commit checks
make evaluate EVAL_ARGS="--strategies raw,rerank"
make evaluate EVAL_SUITE=candidate_pools
```

See [server/README.md](server/README.md) for deployment-specific details and
[evaluation/README.md](evaluation/README.md) for retrieval quality results and
evaluation commands.
