"use client";

import type { FormEvent, ReactNode } from "react";
import { useState } from "react";
import Image from "next/image";
import { ChevronDown, Info, LoaderCircle, RotateCcw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { Pokemon, PokemonSearchCriteria, PokemonTrait } from "../../domain/pokemon";
import { pokemonTraits } from "../../domain/pokemon";
import { usePokemonExplanation } from "../hooks/use-pokemon-explanation";
import { usePokemonSearch } from "../hooks/use-pokemon-search";
import { useRetryCountdown } from "../hooks/use-retry-countdown";

const MAX_TRAITS = 4;
const MAX_NOTE_LENGTH = 150;
const exampleNotes = [
  "I like solving problems independently.",
  "I stay calm when things get busy.",
  "I enjoy looking after my team.",
] as const;

const traitLabels: Record<PokemonTrait, string> = {
  reliable: "Reliable",
  independent: "Independent",
  calm: "Calm",
  curious: "Curious",
  protective: "Protective",
  adaptable: "Adaptable",
};

export function PokemonFinder() {
  const [selectedTraits, setSelectedTraits] = useState<PokemonTrait[]>([]);
  const [note, setNote] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [submittedCriteria, setSubmittedCriteria] = useState<PokemonSearchCriteria | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  const { state: searchState, isPending: isSearching, search, reset: resetSearch } = usePokemonSearch();
  const {
    states: explanationStates,
    lastError: lastExplanationError,
    isPending: isExplaining,
    load: loadExplanation,
    reset: resetExplanations,
  } = usePokemonExplanation();

  const searchError = searchState.status === "error" ? searchState.error : null;
  const {
    seconds: searchCooldown,
    start: startSearchCooldown,
    reset: resetSearchCooldown,
  } = useRetryCountdown();
  const {
    seconds: explanationCooldown,
    start: startExplanationCooldown,
    reset: resetExplanationCooldown,
  } = useRetryCountdown();
  const {
    seconds: rerankingCooldown,
    start: startRerankingCooldown,
    reset: resetRerankingCooldown,
  } = useRetryCountdown();
  const results = searchState.status === "success" ? searchState.data : null;
  const isSearchBlocked = selectedTraits.length === 0 || isSearching || searchCooldown > 0;

  function toggleTrait(trait: PokemonTrait) {
    if (selectedTraits.includes(trait)) {
      setSelectedTraits((traits) => traits.filter((item) => item !== trait));
      setInputError(null);
      return;
    }
    if (selectedTraits.length === MAX_TRAITS) {
      setInputError(`You can select up to ${MAX_TRAITS} traits.`);
      return;
    }
    setSelectedTraits((traits) => [...traits, trait]);
    setInputError(null);
  }

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTraits.length === 0) {
      setInputError("Choose at least one trait to search.");
      return;
    }
    if (searchCooldown > 0) return;

    const criteria: PokemonSearchCriteria = {
      traits: selectedTraits,
      ...(note.trim() ? { note: note.trim() } : {}),
    };
    setInputError(null);
    setExpandedId(null);
    setSubmittedCriteria(criteria);
    resetExplanations();
    const result = await search(criteria);
    if (!result.ok && result.error.retryAfterSeconds !== undefined) {
      startSearchCooldown(result.error.retryAfterSeconds);
    }
    if (
      result.ok &&
      !result.data.retrieval.reranked &&
      result.data.retrieval.retryAfterSeconds !== undefined
    ) {
      startRerankingCooldown(result.data.retrieval.retryAfterSeconds);
    }
  }

  async function toggleResult(pokemon: Pokemon) {
    if (expandedId === pokemon.id) {
      setExpandedId(null);
      return;
    }
    if (!submittedCriteria || explanationCooldown > 0) return;
    setExpandedId(pokemon.id);
    const result = await loadExplanation(pokemon.id, submittedCriteria);
    if (result && !result.ok && result.error.retryAfterSeconds !== undefined) {
      startExplanationCooldown(result.error.retryAfterSeconds);
    }
  }

  function resetAll() {
    setSelectedTraits([]);
    setNote("");
    setInputError(null);
    setExpandedId(null);
    setSubmittedCriteria(null);
    resetSearch();
    resetExplanations();
    resetSearchCooldown();
    resetExplanationCooldown();
    resetRerankingCooldown();
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 sm:py-10">
      <div className="mx-auto w-full max-w-2xl">
        <header className="mb-12 flex items-center justify-between sm:mb-16">
          <div className="flex items-center gap-2.5">
            <Image
              src="/pokeMatcherIcon.png"
              alt="PokéMatcher"
              width={40}
              height={40}
              priority
              className="size-9 rounded-lg sm:size-10"
            />
            <div>
              <p className="text-sm font-medium tracking-tight">Who&apos;s that Pokémon?</p>
              <p className="mt-1 text-sm text-muted-foreground">A character match, not a quiz.</p>
            </div>
          </div>
          <Button type="button" variant="ghost" size="icon-sm" aria-label="About this project" onClick={() => setShowInfo(true)}>
            <Info aria-hidden="true" />
          </Button>
        </header>

        <section aria-labelledby="search-heading">
          <div className="mb-6">
            <h1 id="search-heading" className="text-2xl font-semibold tracking-tight sm:text-3xl">Find your match</h1>
            <p className="mt-2 max-w-xl text-pretty leading-6 text-muted-foreground">
              Pick a few traits and we&apos;ll look for a Pokémon with a similar disposition.
            </p>
          </div>

          <form onSubmit={submitSearch} className="space-y-6">
            <fieldset>
              <legend className="mb-3 text-sm font-medium">Traits</legend>
              <div className="flex flex-wrap gap-2" role="group" aria-describedby="trait-help">
                {pokemonTraits.map((trait) => {
                  const isSelected = selectedTraits.includes(trait);
                  const cannotSelect = !isSelected && selectedTraits.length === MAX_TRAITS;
                  return (
                    <Button
                      key={trait}
                      type="button"
                      variant={isSelected ? "secondary" : "outline"}
                      size="sm"
                      aria-pressed={isSelected}
                      disabled={cannotSelect}
                      onClick={() => toggleTrait(trait)}
                    >
                      {traitLabels[trait]}
                    </Button>
                  );
                })}
              </div>
              <p id="trait-help" className="mt-3 text-xs text-muted-foreground">
                {selectedTraits.length} of {MAX_TRAITS} selected
              </p>
            </fieldset>

            <div>
              <label htmlFor="extra-note" className="mb-2 block text-sm font-medium">
                Extra note <span className="font-normal text-muted-foreground">(optional)</span>
              </label>
              <input
                id="extra-note"
                value={note}
                onChange={(event) => setNote(event.target.value.slice(0, MAX_NOTE_LENGTH))}
                maxLength={MAX_NOTE_LENGTH}
                autoComplete="off"
                placeholder="Anything else worth knowing?"
                className="h-11 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              />
              <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-1.5" aria-label="Example notes">
                  {exampleNotes.map((example) => (
                    <button
                      key={example}
                      type="button"
                      className="rounded-md px-1.5 py-1 text-left text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:bg-muted focus-visible:text-foreground focus-visible:outline-none"
                      onClick={() => setNote(example)}
                    >
                      {example}
                    </button>
                  ))}
                </div>
                <p className="shrink-0 text-xs text-muted-foreground">{note.length}/{MAX_NOTE_LENGTH}</p>
              </div>
            </div>

            {inputError ? <Notice tone="error">{inputError}</Notice> : null}
            {searchError ? (
              <Notice tone="error">
                {searchCooldown > 0 ? `Search limit reached. Try again in ${formatCountdown(searchCooldown)}.` : searchError.message}
              </Notice>
            ) : null}

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button type="submit" size="lg" disabled={isSearchBlocked} className="w-full sm:w-auto">
                {isSearching ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <Search aria-hidden="true" />}
                {isSearching ? "Searching" : searchCooldown > 0 ? `Try again in ${formatCountdown(searchCooldown)}` : "Search"}
              </Button>
              <Button type="button" size="lg" variant="ghost" onClick={resetAll} disabled={isSearching || isExplaining} className="w-full sm:w-auto">
                <RotateCcw aria-hidden="true" />
                Reset
              </Button>
            </div>
          </form>
        </section>

        {results ? (
          <section className="mt-14 border-t border-border pt-8" aria-labelledby="results-heading">
            <div className="mb-5 flex items-baseline justify-between gap-4">
              <div>
                <h2 id="results-heading" className="text-lg font-semibold tracking-tight">Matches</h2>
                <p className="mt-1 text-sm text-muted-foreground">Your five closest results.</p>
              </div>
              <span className="text-sm text-muted-foreground">{results.pokemon.slice(0, 5).length}</span>
            </div>

            {!results.retrieval.reranked && results.retrieval.rerankUnavailableReason ? (
              <Notice tone="neutral">
                Results are available, though the final ranking step is temporarily unavailable.
                {results.retrieval.retryAfterSeconds
                  ? rerankingCooldown > 0
                    ? ` It should be back in ${formatCountdown(rerankingCooldown)}.`
                    : " It should be available again now."
                  : null}
              </Notice>
            ) : null}

            {lastExplanationError && explanationCooldown > 0 ? (
              <Notice tone="error">Explanation limit reached. You can open another match in {formatCountdown(explanationCooldown)}.</Notice>
            ) : null}

            {results.pokemon.length === 0 ? (
              <p className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
                No close matches this time. Try a different combination of traits.
              </p>
            ) : (
              <ul className="divide-y divide-border rounded-lg border border-border">
                {results.pokemon.slice(0, 5).map((pokemon) => {
                  const isExpanded = expandedId === pokemon.id;
                  const explanationState = explanationStates[pokemon.id] ?? { status: "idle" as const };
                  const isUnavailable = explanationCooldown > 0 && !isExpanded;

                  return (
                    <li key={pokemon.id}>
                      <button
                        type="button"
                        className="flex w-full items-center gap-3 px-3 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 sm:px-4"
                        aria-expanded={isExpanded}
                        aria-controls={`explanation-${pokemon.id}`}
                        disabled={isUnavailable}
                        onClick={() => toggleResult(pokemon)}
                      >
                        <span className="flex size-14 shrink-0 items-center justify-center rounded-md bg-muted sm:size-16">
                          <Image src={pokemon.spriteUrl} alt="" width={64} height={64} className="size-[3.25rem] object-contain sm:size-[3.75rem]" />
                        </span>
                        <span className="min-w-0 flex-1 truncate font-medium">{pokemon.name}</span>
                        {explanationState.status === "loading" && isExpanded ? (
                          <LoaderCircle className="size-4 animate-spin text-muted-foreground" aria-label="Loading explanation" />
                        ) : (
                          <ChevronDown className={`size-4 text-muted-foreground transition-transform ${isExpanded ? "rotate-180" : ""}`} aria-hidden="true" />
                        )}
                      </button>

                      {isExpanded ? (
                        <div id={`explanation-${pokemon.id}`} className="border-t border-border bg-muted/30 px-4 py-4 sm:pl-24">
                          {explanationState.status === "loading" || explanationState.status === "idle" ? <p className="text-sm text-muted-foreground">Putting the match into words…</p> : null}
                          {explanationState.status === "success" ? <p className="text-sm leading-6 text-foreground/90">{explanationState.explanation}</p> : null}
                          {explanationState.status === "error" ? (
                            <p className="text-sm leading-6 text-destructive" role="alert">
                              {explanationCooldown > 0 ? `Explanation limit reached. Try again in ${formatCountdown(explanationCooldown)}.` : explanationState.error.message}
                            </p>
                          ) : null}
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        ) : null}
      </div>

      {showInfo ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/20 p-4 backdrop-blur-[1px]" role="presentation" onMouseDown={() => setShowInfo(false)}>
          <section
            className="w-full max-w-sm rounded-xl border border-border bg-background p-5 shadow-lg"
            role="dialog"
            aria-modal="true"
            aria-labelledby="project-info-heading"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="project-info-heading" className="font-semibold tracking-tight">About this project</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  This is a small Pokémon matcher based on the traits you choose. Search finds close candidates; opening one asks for a short explanation of the match.
                </p>
              </div>
              <Button type="button" variant="ghost" size="icon-xs" onClick={() => setShowInfo(false)} aria-label="Close project information">×</Button>
            </div>
            <p className="mt-4 text-xs leading-5 text-muted-foreground">Explanations use a limited service, so they are requested only when you open a result.</p>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function Notice({ children, tone }: Readonly<{ children: ReactNode; tone: "error" | "neutral" }>) {
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={tone === "error" ? "rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2 text-sm text-destructive" : "mb-4 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground"}
    >
      {children}
    </p>
  );
}

function formatCountdown(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return minutes > 0 ? `${minutes}:${String(remainder).padStart(2, "0")}` : `${remainder}s`;
}
