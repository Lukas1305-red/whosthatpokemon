import "server-only";

import { ExplainPokemonMatch } from "../application/explain-pokemon-match";
import { SearchPokemon } from "../application/search-pokemon";
import { PokemonApiRepository } from "../data/pokemon-api-repository";

function createRepository() {
  const baseUrl = process.env.POKEMON_API_BASE_URL ?? "http://localhost:8000";
  return new PokemonApiRepository({ baseUrl });
}

/** The only place that knows which infrastructure implementation is in use. */
export function makeSearchPokemon(): SearchPokemon {
  return new SearchPokemon(createRepository());
}

export function makeExplainPokemonMatch(): ExplainPokemonMatch {
  return new ExplainPokemonMatch(createRepository());
}
