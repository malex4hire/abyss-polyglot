import { useCallback, useEffect, useMemo, useState } from "react";
import { Status, WorkItem } from "./types";

/**
 * Which backend the application talks to, chosen at runtime.
 *
 * The Angular side holds this in an injectable singleton the framework owns. Here it is a
 * hook, so the state is per caller — which is why the selection lives in the top component
 * and is threaded down as props rather than being reachable from anywhere. That difference
 * is not incidental; it is the framework contrast the pair exists to make visible.
 *
 * The list comes from this frontend's own server, which reads it from the manifest. No
 * stack is named anywhere in this module.
 */
export interface BackendOption {
  id: string;
  label: string;
}

export function useBackends() {
  const [options, setOptions] = useState<BackendOption[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetch("/__backends")
      .then((response) => response.json())
      .then((body: { backends: BackendOption[] }) => {
        if (cancelled) return;
        setOptions(body.backends ?? []);
        setSelected((current) => current || body.backends?.[0]?.id || "");
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return { options, selected, select: setSelected };
}

/** Every URL is built from the selection at call time, so a switch needs no reload. */
export function useTracker(backend: string) {
  const base = backend ? `/api/${backend}` : "";

  const list = useCallback(
    async (filters: { status?: string; tag?: string }): Promise<WorkItem[]> => {
      const query = new URLSearchParams();
      if (filters.status) query.set("status", filters.status);
      if (filters.tag) query.set("tag", filters.tag);
      const suffix = query.toString() ? `?${query}` : "";
      const response = await fetch(`${base}/work-items${suffix}`);
      if (!response.ok) throw new Error(`work-items responded ${response.status}`);
      return ((await response.json()) as { items: WorkItem[] }).items ?? [];
    },
    [base],
  );

  const create = useCallback(
    async (draft: Record<string, unknown>): Promise<void> => {
      const response = await fetch(`${base}/work-items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (!response.ok) throw new Error(`create responded ${response.status}`);
    },
    [base],
  );

  const transition = useCallback(
    async (id: string, status: Status): Promise<{ rejected?: Record<string, string> }> => {
      const response = await fetch(`${base}/work-items/${id}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      // A refusal is a 422 carrying the typed rejection, not an error to swallow.
      if (response.status === 422) {
        const body = (await response.json()) as { rejected?: Record<string, string> };
        return { rejected: body.rejected ?? {} };
      }
      if (!response.ok) throw new Error(`transition responded ${response.status}`);
      return {};
    },
    [base],
  );

  const archive = useCallback(
    async (id: string): Promise<void> => {
      await fetch(`${base}/work-items/${id}/archive`, { method: "POST" });
    },
    [base],
  );

  const workload = useCallback(async (): Promise<Record<string, number>> => {
    const response = await fetch(`${base}/workload`);
    if (!response.ok) throw new Error(`workload responded ${response.status}`);
    return ((await response.json()) as { byAssignee: Record<string, number> }).byAssignee ?? {};
  }, [base]);

  // Memoised as one object. Each callback is already stable, but returning a fresh
  // object literal gives the caller a new identity every render — and a caller that puts
  // it in a useCallback dependency list then rebuilds its own callback every render, and
  // an effect depending on that runs forever. The page rendered and stayed on "loading…"
  // with no error anywhere: the request was being made, and remade, indefinitely.
  return useMemo(
    () => ({ list, create, transition, archive, workload }),
    [list, create, transition, archive, workload],
  );
}
