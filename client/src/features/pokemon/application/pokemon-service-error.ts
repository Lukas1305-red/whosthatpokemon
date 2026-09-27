/** A transport-agnostic failure that presentation can safely turn into feedback. */
export class PokemonServiceError extends Error {
  constructor(message: string, readonly status: number, readonly retryAfterSeconds?: number) {
    super(message);
    this.name = "PokemonServiceError";
  }
}
