"use client";

import { useCallback, useEffect, useState } from "react";

/** Turns a server-provided Retry-After duration into a live client-side countdown. */
export function useRetryCountdown() {
  const [retryAt, setRetryAt] = useState<number | null>(null);
  const [now, setNow] = useState<number | null>(null);

  const start = useCallback((retryAfterSeconds: number) => {
    const currentTime = Date.now();
    setRetryAt(currentTime + retryAfterSeconds * 1_000);
    setNow(currentTime);
  }, []);

  const reset = useCallback(() => {
    setRetryAt(null);
    setNow(null);
  }, []);

  useEffect(() => {
    if (retryAt === null) return;
    const interval = window.setInterval(() => {
      const currentTime = Date.now();
      if (currentTime >= retryAt) {
        window.clearInterval(interval);
        setRetryAt(null);
        setNow(null);
        return;
      }
      setNow(currentTime);
    }, 1_000);
    return () => window.clearInterval(interval);
  }, [retryAt]);

  const seconds = retryAt === null || now === null ? 0 : Math.max(0, Math.ceil((retryAt - now) / 1_000));
  return { seconds, start, reset } as const;
}
