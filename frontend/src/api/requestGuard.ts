/**
 * Stale-response guard.
 * Owner: Shehani.
 *
 * Each call to `next()` aborts the previous in-flight request and returns a
 * ticket. A response may only be applied while `ticket.isCurrent()` is true,
 * so a slow response for an old farm/scenario can never overwrite a newer one.
 */
export interface RequestTicket {
  signal: AbortSignal;
  isCurrent: () => boolean;
}

export interface LatestRequest {
  next: () => RequestTicket;
  cancel: () => void;
}

export function createLatestRequest(): LatestRequest {
  let seq = 0;
  let controller: AbortController | null = null;

  return {
    next() {
      controller?.abort();
      controller = new AbortController();
      const mine = ++seq;
      const signal = controller.signal;
      return { signal, isCurrent: () => mine === seq && !signal.aborted };
    },
    cancel() {
      seq++;
      controller?.abort();
      controller = null;
    },
  };
}

export function isAbortError(err: unknown): boolean {
  return (
    typeof err === "object" &&
    err !== null &&
    "name" in err &&
    ((err as { name: unknown }).name === "AbortError" || (err as { name: unknown }).name === "CanceledError")
  );
}
