"use client";

import { useState, useTransition } from "react";

import type { PokemonSearchResult } from "../../domain/pokemon";
import {
  searchPokemonAction,
  type ActionError,
  type ActionResult,
} from "../actions/pokemon-actions";

export type PokemonSearchState =
  | Readonly<{ status: "idle"; data?: undefined; error?: undefined }>
  | Readonly<{ status: "loading"; data?: undefined; error?: undefined }>
  | Readonly<{ status: "success"; data: PokemonSearchResult; error?: undefined }>
  | Readonly<{ status: "error"; data?: undefined; error: ActionError }>;

/** Presentation state only: no API fields or validation rules appear in the UI. */
export function usePokemonSearch() {
  const [state, setState] = useState<PokemonSearchState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();

  function search(input: unknown): Promise<ActionResult<PokemonSearchResult>> {
    return new Promise((resolve) => {
      startTransition(async () => {
      setState({ status: "loading" });
      const result = await searchPokemonAction(input);
      setState(
        result.ok
          ? { status: "success", data: result.data }
          : { status: "error", error: result.error },
      );
        resolve(result);
      });
    });
  }

  function reset() {
    setState({ status: "idle" });
  }

  return { state, isPending, search, reset } as const;
}
