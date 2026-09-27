# Client

This is a Next.js App Router client organized by feature and dependency direction.
The `pokemon` feature is a complete, responsive vertical slice over the existing
Python API.

## Structure

```text
src/
  app/                         # Next.js routes, layouts, and route-level composition
  features/
    pokemon/
      domain/                  # Entities, value validation, ports (no React/Next/HTTP)
      application/             # Use cases that depend only on domain ports
      data/                    # API repository and transport-to-domain mapping
      composition/             # Server-only dependency wiring
      presentation/            # Components, view hooks, and Server Action boundary
```

Dependencies point inwards:

```text
presentation -> application -> domain
data -----------implements---> domain port
composition ----wires--------> application + data
```

`app/` stays thin. Pages compose feature presentation components; they do not hold
API calls, business rules, or long-lived state. Pages and layouts are Server
Components by default. Add `"use client"` only to the smallest interactive
component or hook that needs browser state or events.

## Boundaries in the Pokémon feature

- `domain/pokemon.ts` owns Pokémon vocabulary and search validation.
- `domain/pokemon-repository.ts` defines the repository interface used by use cases.
- `application/` orchestrates a task without knowing where its data comes from.
- `data/pokemon-api-repository.ts` is the only location that knows the Python API's
  JSON shape (`sprite_url`, `searchRequest`, and so on). It is server-only and uses
  `cache: "no-store"` because searches are dynamic.
- `composition/server.ts` selects the concrete repository using the private
  `POKEMON_API_BASE_URL` environment variable.
- `presentation/actions/` is a thin Server Action adapter. Client hooks call it and
  receive a serializable success/error result; they never call the Python API directly.

## User experience

The home page uses the installed shadcn `Button` primitive for its controls. Trait
selection is validated in the browser (one to four selections and a 150-character
note) and again at the server boundary. A search returns up to five vertical result
rows. Opening a row lazily requests its explanation; only one row can be open, and
successful explanations are cached for that result set to avoid needless requests.

Both search and explanation rate limits honor the API's `Retry-After` header. The UI
shows a live countdown and disables the relevant control until another request is
allowed.

## Adding a capability

For a new Pokémon capability, first add a domain type or port if needed, then a use
case, extend or add a data adapter, wire it in `composition/server.ts`, and expose
it through a Server Action and presentation component or hook. For a wholly new
product area, create another folder under `features/` with the same layers. Move
code to a `shared/` module only after two features genuinely need it.

## Configuration

Copy `.env.example` to `.env.local` and set `POKEMON_API_BASE_URL` for the Python
service. This variable intentionally does not use the `NEXT_PUBLIC_` prefix, so it
cannot be included in the browser bundle.
