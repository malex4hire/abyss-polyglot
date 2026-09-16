import { WorkItem } from "./types";

/**
 * Total priority per assignee.
 *
 * Deliberately the expensive part of the render, extracted so the component that calls
 * it can wrap it in useMemo. The memoisation lives there, where the caching decision is
 * actually made; this is only the work being cached.
 */
export function summarise(items: WorkItem[]): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const item of items) {
    totals[item.assignee] = (totals[item.assignee] ?? 0) + item.priority;
  }
  return totals;
}
