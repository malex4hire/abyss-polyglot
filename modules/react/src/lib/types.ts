export type Status = "OPEN" | "IN_PROGRESS" | "BLOCKED" | "DONE" | "CANCELLED";

export interface WorkItem {
  id: string;
  title: string;
  status: Status;
  priority: number;
  assignee: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  archivedAt: string | null;
}

/**
 * The one OpenAPI contract in contract/openapi.yaml, consumed unmodified.
 *
 * The base URL arrives from the environment rather than being written here. A port
 * literal in this file would be a second place ports are declared, and the first one to
 * go stale, which is why stacks/manifest.yaml is the only place they are written.
 */
export const API_BASE: string = (import.meta as any).env?.VITE_API_BASE ?? "";
