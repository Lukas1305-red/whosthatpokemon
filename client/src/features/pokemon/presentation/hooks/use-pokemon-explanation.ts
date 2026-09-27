"use client";

import { useState, useTransition } from "react";

import type { PokemonSearchCriteria } from "../../domain/pokemon";
import {
  explainPokemonMatchAction,
  type ActionError,
  type ActionResult,
} from "../actions/pokemon-actions";

export type ExplanationState =
  | Readonly<{ status: "idle" }>
  | Readonly<{ status: "loading" }>
  | Readonly<{ status: "success"; explanation: string }>
  | Readonly<{ status: "error"; error: ActionError }>;

/** Caches successful explanations for the current result set to conserve the API limit. */
export function usePokemonExplanation() {
  const [states, setStates] = useState<Record<string, ExplanationState>>({});
  const [lastError, setLastError] = useState<ActionError | null>(null);
  const [isPending, startTransition] = useTransition();

  function reset() {
    setStates({});
    setLastError(null);
  }

  function load(
    pokemonId: string,
    searchCriteria: PokemonSearchCriteria,
  ): Promise<ActionResult<string> | undefined> {
    const current = states[pokemonId];
    if (current?.status === "loading" || current?.status === "success") {
      return Promise.resolve(undefined);
    }

    return new Promise((resolve) => {
      startTransition(async () => {
        setStates((previous) => ({ ...previous, [pokemonId]: { status: "loading" } }));
        const result = await explainPokemonMatchAction({ pokemonId, searchCriteria });
        if (result.ok) {
          setStates((previous) => ({
            ...previous,
            [pokemonId]: { status: "success", explanation: result.data },
          }));
          setLastError(null);
          resolve(result);
          return;
        }

        setStates((previous) => ({
          ...previous,
          [pokemonId]: { status: "error", error: result.error },
        }));
        setLastError(result.error);
        resolve(result);
      });
    });
  }

  return { states, lastError, isPending, load, reset } as const;
}
