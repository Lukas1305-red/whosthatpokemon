import type { PokemonSearchCriteria, PokemonSearchResult } from "./pokemon";

/** A port owned by the domain/application layers; infrastructure implements it. */
export interface PokemonRepository {
  search(criteria: PokemonSearchCriteria): Promise<PokemonSearchResult>;
  explain(input: ExplainPokemonInput): Promise<string>;
}

export type ExplainPokemonInput = Readonly<{
  pokemonId: string;
  searchCriteria: PokemonSearchCriteria;
}>;
