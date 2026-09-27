import type { PokemonRepository } from "../domain/pokemon-repository";
import type { PokemonSearchCriteria, PokemonSearchResult } from "../domain/pokemon";

/** A framework-free use case that is easy to unit test with a fake repository. */
export class SearchPokemon {
  constructor(private readonly repository: PokemonRepository) {}

  execute(criteria: PokemonSearchCriteria): Promise<PokemonSearchResult> {
    return this.repository.search(criteria);
  }
}
