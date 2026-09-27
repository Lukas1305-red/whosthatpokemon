"use server";

import { PokemonServiceError } from "../../application/pokemon-service-error";
import { makeExplainPokemonMatch, makeSearchPokemon } from "../../composition/server";
import {
  createPokemonSearchCriteria,
  InvalidPokemonSearchError,
  type PokemonSearchResult,
} from "../../domain/pokemon";

export type ActionResult<T> =
  | Readonly<{ ok: true; data: T }>
  | Readonly<{ ok: false; error: ActionError }>;

export type ActionError = Readonly<{
  message: string;
  retryAfterSeconds?: number;
}>;

/** A thin Next.js boundary between client-side presentation and use cases. */
export async function searchPokemonAction(input: unknown): Promise<ActionResult<PokemonSearchResult>> {
  try {
    const criteria = createPokemonSearchCriteria(input);
    return { ok: true, data: await makeSearchPokemon().execute(criteria) };
  } catch (error) {
    return { ok: false, error: toActionError(error) };
  }
}

export async function explainPokemonMatchAction(input: unknown): Promise<ActionResult<string>> {
  try {
    if (!isRecord(input) || typeof input.pokemonId !== "string") {
      throw new InvalidPokemonSearchError("Choose a Pokémon before requesting an explanation.");
    }
    const searchCriteria = createPokemonSearchCriteria(input.searchCriteria);
    const explanation = await makeExplainPokemonMatch().execute({
      pokemonId: input.pokemonId,
      searchCriteria,
    });
    return { ok: true, data: explanation };
  } catch (error) {
    return { ok: false, error: toActionError(error) };
  }
}

function toActionError(error: unknown): ActionError {
  if (error instanceof InvalidPokemonSearchError) return { message: error.message };
  if (error instanceof PokemonServiceError) {
    return {
      message: error.message,
      ...(error.retryAfterSeconds !== undefined ? { retryAfterSeconds: error.retryAfterSeconds } : {}),
    };
  }
  return { message: "Something went wrong. Please try again." };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
