# Pokémon Finder API

A FastAPI service that finds Pokémon matching a person's preferred traits. It
uses Cohere embeddings for retrieval, optional reranking, and Anthropic to
generate a short explanation for a selected result.

## Run locally

1. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` and
   `COHERE_API_KEY`.
2. Ensure the local Chroma index exists at `data/chroma`. To generate it from
   source data, run the `make pipeline`.
3. Start the API:

   ```sh
   make server
   ```

The API is available at `http://localhost:8000`; interactive API documentation
is at `/docs`.

## Docker deployment

The deployment image deliberately does **not** include `data/`. The Chroma
index is ignored by Git and mounted at runtime, which keeps an untracked local
index out of source images and makes its lifecycle explicit.

```sh
cp .env.example .env
# Set the two provider keys and production host/origin values in .env.
docker compose up --build
```

The API container runs as a non-root user with one Uvicorn worker. Chroma stays
embedded for this single-instance deployment; do not add replicas until the
index moves to a server-backed vector store.

For a hosted deployment, upload or otherwise seed the `data/chroma` directory
to a persistent volume mounted at `/app/data/chroma`. The process needs write
access to that volume because the embedded Chroma client maintains local state.

## Production configuration

Configure these through your hosting provider's encrypted environment secrets:

- `ANTHROPIC_API_KEY` and `COHERE_API_KEY`: required provider credentials.
- `ALLOWED_ORIGINS`: comma-separated Next.js client origins, for example
  `https://app.example.com`. Do not use `*` for a production browser client.
- `TRUSTED_HOSTS`: comma-separated API domains, for example
  `api.example.com`.
- `CHROMA_DATA_PATH`: defaults to `data/chroma`; set to `/app/data/chroma` in
  containers.
- `EXPLAIN_RATE_LIMIT_REQUESTS`: defaults to 3 per minute per client.
- `ANTHROPIC_TIMEOUT_SECONDS`: defaults to 15 seconds; retries default to 0.
- `LLM_ENABLED`: set to `false` to immediately disable all paid explanation
  calls while leaving search available.
- `EXPLAIN_DAILY_LLM_BUDGET`: defaults to 25 paid cache-miss explanations per
  UTC day. Docker Compose provides Redis to preserve this counter and share
  cached explanations between API instances. Set `REDIS_URL` to a managed Redis
  endpoint for hosted deployment.

Use `/health` for liveness and `/ready` for readiness. Readiness checks only
the local Chroma index, so health probes never create paid provider calls.

Before exposing the API publicly, configure HTTPS at the hosting edge, set the
two host/origin allowlists, and enforce an equivalent request-size limit at the
reverse proxy.

## Verification

```sh
make test
```

GitHub Actions runs the full test suite and builds the deployment image on pull
requests, pushes to `main`, and manual runs.
