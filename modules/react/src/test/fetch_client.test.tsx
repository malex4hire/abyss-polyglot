import { describe, expect, it, vi } from "vitest";
import { render, screen, renderHook, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";

function item(id: string, over: Partial<WorkItem> = {}): WorkItem {
  return {
    id, title: `title-${id}`, status: "OPEN", priority: 5, assignee: "avery",
    createdAt: AT, updatedAt: AT, tags: ["backend"], archivedAt: null, ...over,
  };
}

import { fetchWorkItems } from "../lib/api";

it("fetch-client: a non-2xx is a normal Response, so the check is explicit", async () => {
  const ok = vi.fn().mockResolvedValue({
    ok: true, status: 200, json: async () => ({ items: [item("WI-1")] }),
  });
  vi.stubGlobal("fetch", ok);
  await expect(fetchWorkItems({ tag: "backend" })).resolves.toHaveLength(1);
  expect(ok.mock.calls[0][0]).toContain("tag=backend");

  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  await expect(fetchWorkItems()).rejects.toThrow(/503/);
  vi.unstubAllGlobals();
});


it("fetch-client: query values are escaped, not pasted into the URL", async () => {
  // The assertions above pass against a query string concatenated by hand, because for
  // ordinary values the two produce byte-identical URLs. The difference is what happens to
  // a value that means something in a URL — a space, an ampersand — and that is the only
  // place URLSearchParams earns its keep.
  const seen: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    seen.push(url);
    return { ok: true, status: 200, json: async () => ({ items: [] }) };
  }));

  await fetchWorkItems({ tag: "back end&status=DONE" });

  expect(seen[0]).not.toContain("back end&status=DONE");
  expect(seen[0]).toContain("back+end%26status%3DDONE");

  vi.unstubAllGlobals();
});
