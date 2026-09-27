import type { ExplainPokemonInput, PokemonRepository } from "../domain/pokemon-repository";

/** Kept separate so explanation policy can evolve independently of search. */
export class ExplainPokemonMatch {
  constructor(private readonly repository: PokemonRepository) {}

  execute(input: ExplainPokemonInput): Promise<string> {
    if (!input.pokemonId.trim()) {
      throw new Error("A Pokémon must be selected before requesting an explanation.");
    }
    return this.repository.explain(input);
  }
}
