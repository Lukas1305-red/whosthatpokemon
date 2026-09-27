/** The language of the Pokémon feature, independent of React and HTTP. */
export const pokemonTraits = [
  "reliable",
  "independent",
  "calm",
  "curious",
  "protective",
  "adaptable",
] as const;

export type PokemonTrait = (typeof pokemonTraits)[number];

export type Pokemon = Readonly<{
  id: string;
  name: string;
  spriteUrl: string;
}>;

export type RetrievalMetadata = Readonly<{
  reranked: boolean;
  rerankUnavailableReason?: "rate_limited" | "cohere_error";
  retryAfterSeconds?: number;
}>;

export type PokemonSearchResult = Readonly<{
  pokemon: readonly Pokemon[];
  retrieval: RetrievalMetadata;
}>;

export type PokemonSearchCriteria = Readonly<{
  traits: readonly PokemonTrait[];
  note?: string;
}>;

export class InvalidPokemonSearchError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidPokemonSearchError";
  }
}

/** Validates untrusted input at the boundary; business rules live here, not in React. */
export function createPokemonSearchCriteria(input: unknown): PokemonSearchCriteria {
  if (!isRecord(input) || !Array.isArray(input.traits)) {
    throw new InvalidPokemonSearchError("Choose at least one trait.");
  }
  if (input.traits.length < 1 || input.traits.length > 4) {
    throw new InvalidPokemonSearchError("Choose between one and four traits.");
  }
  if (!input.traits.every(isPokemonTrait)) {
    throw new InvalidPokemonSearchError("One or more selected traits are invalid.");
  }

  const traits = [...input.traits];
  if (new Set(traits).size !== traits.length) {
    throw new InvalidPokemonSearchError("Choose each trait only once.");
  }
  if (input.note !== undefined && typeof input.note !== "string") {
    throw new InvalidPokemonSearchError("The note must be text.");
  }

  const note = input.note?.trim();
  if (note && note.length > 150) {
    throw new InvalidPokemonSearchError("The note can be at most 150 characters.");
  }
  return { traits, ...(note ? { note } : {}) };
}

function isPokemonTrait(value: unknown): value is PokemonTrait {
  return typeof value === "string" && pokemonTraits.includes(value as PokemonTrait);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
