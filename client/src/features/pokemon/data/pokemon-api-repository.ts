import "server-only";

import { PokemonServiceError } from "../application/pokemon-service-error";
import type { ExplainPokemonInput, PokemonRepository } from "../domain/pokemon-repository";
import type {
  Pokemon,
  PokemonSearchCriteria,
  PokemonSearchResult,
  RetrievalMetadata,
} from "../domain/pokemon";

type Fetch = typeof fetch;
type PokemonApiRepositoryOptions = Readonly<{ baseUrl: string; fetch?: Fetch }>;

/** Maps the Python API transport format to domain types. */
export class PokemonApiRepository implements PokemonRepository {
  private readonly fetch: Fetch;
  private readonly baseUrl: URL;

  constructor({ baseUrl, fetch: fetchImplementation = fetch }: PokemonApiRepositoryOptions) {
    this.baseUrl = new URL(baseUrl);
    this.fetch = fetchImplementation;
  }

  async search(criteria: PokemonSearchCriteria): Promise<PokemonSearchResult> {
    const payload = await this.request("/search", {
      traits: criteria.traits,
      ...(criteria.note ? { note: criteria.note } : {}),
    });
    return parseSearchResponse(payload);
  }

  async explain(input: ExplainPokemonInput): Promise<string> {
    const payload = await this.request("/explain", {
      pokemon_id: input.pokemonId,
      searchRequest: {
        traits: input.searchCriteria.traits,
        ...(input.searchCriteria.note ? { note: input.searchCriteria.note } : {}),
      },
    });
    if (!isRecord(payload) || typeof payload.explanation !== "string") {
      throw new PokemonServiceError("The Pokémon API returned an invalid explanation.", 502);
    }
    return payload.explanation;
  }

  private async request(path: string, body: unknown): Promise<unknown> {
    let response: Response;
    try {
      response = await this.fetch(new URL(path, this.baseUrl), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        // Search results are dynamic and must not be served from a stale cache.
        cache: "no-store",
      });
    } catch {
      throw new PokemonServiceError("Unable to reach the Pokémon service.", 503);
    }

    const payload = await readJson(response);
    if (!response.ok) {
      throw new PokemonServiceError(errorMessage(payload, response.status), response.status, retryAfter(response));
    }
    return payload;
  }
}

function parseSearchResponse(payload: unknown): PokemonSearchResult {
  if (!isRecord(payload) || !Array.isArray(payload.pokemon) || !isRecord(payload.retrieval)) {
    throw new PokemonServiceError("The Pokémon API returned an invalid search response.", 502);
  }
  return { pokemon: payload.pokemon.map(parsePokemon), retrieval: parseRetrieval(payload.retrieval) };
}

function parsePokemon(value: unknown): Pokemon {
  if (!isRecord(value) || typeof value.id !== "string" || typeof value.name !== "string" || typeof value.sprite_url !== "string") {
    throw new PokemonServiceError("The Pokémon API returned an invalid Pokémon.", 502);
  }
  return { id: value.id, name: value.name, spriteUrl: value.sprite_url };
}

function parseRetrieval(value: Record<string, unknown>): RetrievalMetadata {
  if (typeof value.reranked !== "boolean") {
    throw new PokemonServiceError("The Pokémon API returned invalid retrieval metadata.", 502);
  }
  const reason = value.rerank_unavailable_reason;
  const retryAfterSeconds = value.retry_after_seconds;
  // FastAPI serializes optional values as `null`, while TypeScript represents
  // omitted optional properties as `undefined`. Both mean "not provided" here.
  if (
    reason !== undefined &&
    reason !== null &&
    reason !== "rate_limited" &&
    reason !== "cohere_error"
  ) {
    throw new PokemonServiceError("The Pokémon API returned invalid retrieval metadata.", 502);
  }
  if (
    retryAfterSeconds !== undefined &&
    retryAfterSeconds !== null &&
    (typeof retryAfterSeconds !== "number" ||
      !Number.isInteger(retryAfterSeconds) ||
      retryAfterSeconds < 0)
  ) {
    throw new PokemonServiceError("The Pokémon API returned invalid retrieval metadata.", 502);
  }
  return {
    reranked: value.reranked,
    ...(reason === "rate_limited" || reason === "cohere_error"
      ? { rerankUnavailableReason: reason }
      : {}),
    ...(typeof retryAfterSeconds === "number" ? { retryAfterSeconds } : {}),
  };
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function errorMessage(payload: unknown, status: number): string {
  return isRecord(payload) && typeof payload.detail === "string"
    ? payload.detail
    : `The Pokémon service returned an error (${status}).`;
}

function retryAfter(response: Response): number | undefined {
  const value = response.headers.get("Retry-After");
  return value && /^\d+$/.test(value) ? Number(value) : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
