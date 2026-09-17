import { useCallback, useEffect, useState } from "react";
import { fetchWorkItems } from "./api";
import { WorkItem } from "./types";

export interface FetchState {
  items: WorkItem[];
  loading: boolean;
  error: string | null;
}

/**
 * Load work items, and expose the loading and error states with them.
 *
 * A custom hook is a function that calls other hooks, nothing more. It shares stateful
 * logic between components without the wrapper nesting that render props and HOCs
 * produced, and because it is a plain function its rules still apply: called
 * unconditionally, at the top level, so React can match each call to its slot.
 *
 * The Angular counterpart is an injectable service, which the container constructs once
 * and shares. This is the opposite: called per component, state per caller.
 *
 * The loader is a parameter defaulting to the real one, so a test of the hook supplies
 * its own and stays independent of how the request is made.
 */
export function useWorkItems(
  load: () => Promise<WorkItem[]> = fetchWorkItems,
): FetchState & { reload: () => void } {
  const [state, setState] = useState<FetchState>({
    items: [],
    loading: true,
    error: null,
  });

  const reload = useCallback(() => {
    setState((current) => ({ ...current, loading: true, error: null }));
    load()
      .then((items) => setState({ items, loading: false, error: null }))
      .catch((cause: Error) =>
        setState({ items: [], loading: false, error: cause.message }),
      );
  }, [load]);

  useEffect(reload, [reload]);

  return { ...state, reload };
}
