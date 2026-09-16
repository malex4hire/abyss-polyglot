import { FetchState } from "../lib/useWorkItems";
import { ReactNode } from "react";

export interface FetchStatesProps extends FetchState {
  children: ReactNode;
}

/**
 * Render the three states a request can be in.
 *
 * Loading, failed and loaded are not decorations on the happy path — they are the states
 * the component actually has, and naming all three is what stops a UI that renders an
 * empty list while it is still loading, or nothing at all when the request failed.
 *
 * The order matters: error before empty, because a failed request and a genuinely empty
 * result look identical if you check length first.
 */
export function FetchStates({ items, loading, error, children }: FetchStatesProps) {
  if (loading) {
    return <p data-testid="state">loading…</p>;
  }
  if (error) {
    return <p data-testid="state">could not load: {error}</p>;
  }
  if (items.length === 0) {
    return <p data-testid="state">nothing here yet</p>;
  }
  return <>{children}</>;
}
