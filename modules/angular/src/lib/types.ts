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
 * The one OpenAPI contract in contract/openapi.yaml, consumed unmodified. The base URL
 * comes from the environment; a port literal here would be a second place ports are
 * declared, and stacks/manifest.yaml is meant to be the only one.
 */
export const API_BASE: string = (import.meta as any).env?.VITE_API_BASE ?? "";
