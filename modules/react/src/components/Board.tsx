import { memo, useEffect, useMemo, useReducer, useState } from "react";
import { WorkItemList } from "./WorkItemList";
import { FetchStates } from "./FetchStates";
import { Panel } from "./Panel";
import { StatusBadge } from "./StatusBadge";
import { WorkItemRow } from "./WorkItemRow";
import { DraftForm } from "./DraftForm";
import { boardReducer, BoardState } from "../lib/reducer";
import { summarise } from "../lib/summary";
import { useBoardSettings } from "../lib/BoardContext";
import { useWorkItems } from "../lib/useWorkItems";
import { WorkItem } from "../lib/types";
import { EmptyState } from "./EmptyState";
import { Placeholder } from "./Placeholder";
import { Heading } from "./Heading";
import { useDocumentTitle, useSelectionCount } from "./Counter";

const INITIAL: BoardState = { items: [], selected: null };

/** The board. Composes the module's components; no test targets it directly. */
export function Board() {
  const settings = useBoardSettings();
  const { items, loading, error, reload } = useWorkItems();
  const [state, dispatch] = useReducer(boardReducer, INITIAL);
  const [filter, setFilter] = useState("");
  const [selectionCount, bumpSelection] = useSelectionCount();
  useDocumentTitle(`work items (${selectionCount})`);

  useEffect(() => {
    dispatch({ type: "loaded", items });
  }, [items]);

  const visible = state.items.filter((item) =>
    filter ? item.tags.includes(filter) : true,
  );

  return (
    <Panel title="work items" actions={<Totals items={visible} />}>
      <Heading count={items.length} assignee="everyone" />
      <Placeholder />
      <p data-testid="page-size">page size {settings.pageSize}</p>
      <FilterBox value={filter} onChange={setFilter} />
      <DraftForm onSubmit={() => reload()} />
      <FetchStates items={visible} loading={loading} error={error}>
        <WorkItemList
          items={visible.slice(0, settings.pageSize)}
          onSelect={(id) => {
            bumpSelection();
            dispatch({ type: "selected", id });
          }}
        />
      </FetchStates>
      {state.selected ? <Selected id={state.selected} items={visible} /> : <EmptyState />}
    </Panel>
  );
}

function Selected({ id, items }: { id: string; items: WorkItem[] }) {
  const item = items.find((candidate) => candidate.id === id);
  if (!item) {
    return null;
  }
  return (
    <>
      <WorkItemRow item={item} onSelect={() => undefined} />
      <p data-testid="selected">
        {item.title}{" "}
        <StatusBadge status={item.status} archived={item.archivedAt !== null} />
      </p>
    </>
  );
}

/**
 * Totals, recomputed only when the items change.
 *
 * useMemo caches a value against a dependency array; memo caches a whole render against
 * props. Both trade memory and a comparison for work skipped, and both are wrong by
 * default. Measure first, because an unnecessary useMemo costs an allocation and a
 * comparison on every render and buys nothing.
 *
 * The dependency array is the contract: leave something out and the cached value goes
 * stale, which is a bug the linter can see and the type checker cannot.
 */
export const Totals = memo(function Totals({ items }: { items: WorkItem[] }) {
  const totals = useMemo(() => summarise(items), [items]);
  return (
    <span data-testid="totals">
      {Object.entries(totals)
        .map(([assignee, total]) => `${assignee}:${total}`)
        .join(" ")}
    </span>
  );
});

/**
 * Handle typing in the filter box.
 *
 * React attaches one listener at the root and dispatches synthetic events, so the
 * handler receives a normalised event rather than whatever the browser produced. The
 * handler is a prop, not an addEventListener call, which means it is removed with the
 * component and cannot leak.
 *
 * Angular writes the same thing as (input)="..." in the template, which is a binding
 * rather than a function reference.
 */
export function FilterBox({
  value,
  onChange,
}: {
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <input
      aria-label="filter"
      data-testid="filter"
      value={value}
      onChange={(event) => onChange(event.target.value.trim())}
    />
  );
}
