import { WorkItem } from "../lib/types";

export interface WorkItemRowProps {
  item: WorkItem;
  onSelect: (id: string) => void;
}

/**
 * One row, told everything it needs.
 *
 * Props are the component's parameters: read-only, flowing one way, and the whole of its
 * input. This component holds no state and asks for nothing — give it the same props and
 * it renders the same output, which is what makes it trivially testable.
 *
 * Angular's equivalent is an @Input, declared on the class and set by the parent's
 * template binding rather than passed as a function argument.
 */
export function WorkItemRow({ item, onSelect }: WorkItemRowProps) {
  return (
    <li data-testid="row">
      <button type="button" onClick={() => onSelect(item.id)}>
        {item.title}
      </button>
      <span data-testid="row-status">{item.status}</span>
      <span data-testid="row-priority">{item.priority}</span>
    </li>
  );
}
