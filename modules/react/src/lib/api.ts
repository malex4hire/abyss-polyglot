import { API_BASE, WorkItem } from "./types";

/**
 * Talk to the backend with the platform's own fetch.
 *
 * There is no client library here and no interceptor chain: fetch returns a Response,
 * and a non-2xx is a perfectly normal Response rather than a thrown error — which is the
 * detail everyone forgets, so the check is explicit. Angular's HttpClient returns an
 * Observable and throws on non-2xx; this returns a Promise and does not.
 */
export async function fetchWorkItems(
  params: { status?: string; tag?: string } = {},
): Promise<WorkItem[]> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.tag) query.set("tag", params.tag);
  const suffix = query.toString() ? `?${query.toString()}` : "";

  const response = await fetch(`${API_BASE}/work-items${suffix}`);
  if (!response.ok) {
    throw new Error(`work-items responded ${response.status}`);
  }
  const body = (await response.json()) as { items: WorkItem[] };
  return body.items;
}

export async function transition(id: string, status: string): Promise<Response> {
  return fetch(`${API_BASE}/work-items/${id}/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}
