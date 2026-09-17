import { WorkItem } from "../lib/types";

export interface WorkItemListProps {
  items: WorkItem[];
  onSelect: (id: string) => void;
}

/**
 * Render a list, keyed by identity.
 *
 * The key tells React which element corresponds to which item across renders, so it can
 * move a row instead of rebuilding it, and so state living inside a row follows the
 * right row. Using the array index here would mean deleting the first item silently
 * hands its state to its successor, which is the bug this exists to prevent.
 */
export function WorkItemList({ items, onSelect }: WorkItemListProps) {
  return (
    <ul data-testid="list">
      {items.map((item) => (
        <li key={item.id} data-testid="row">
          <button type="button" onClick={() => onSelect(item.id)}>
            {item.title}
          </button>
        </li>
      ))}
    </ul>
  );
}
