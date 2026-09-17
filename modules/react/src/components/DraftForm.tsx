import { useState } from "react";
import { DraftItem, validateDraft } from "../lib/validation";

export interface DraftFormProps {
  onSubmit: (draft: DraftItem) => void;
}

const EMPTY: DraftItem = { title: "", priority: "", assignee: "" };

/**
 * An input whose value is React state.
 *
 * The DOM node holds no truth of its own: value comes from state and every keystroke
 * goes through onChange, so the component always knows what is typed and can normalise,
 * disable or validate it. Drop the onChange and the field appears frozen, which is the
 * classic symptom of a controlled input missing half its wiring.
 */
export function DraftForm({ onSubmit }: DraftFormProps) {
  const [draft, setDraft] = useState<DraftItem>(EMPTY);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function update(field: keyof DraftItem, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  return (
    <form
      data-testid="draft-form"
      onSubmit={(event) => {
        event.preventDefault();
        const found = validateDraft(draft);
        setErrors(found);
        if (Object.keys(found).length === 0) {
          onSubmit(draft);
          setDraft(EMPTY);
        }
      }}
    >
      <label>
        title
        <input
          aria-label="title"
          value={draft.title}
          onChange={(event) => update("title", event.target.value)}
        />
      </label>
      <label>
        priority
        <input
          aria-label="priority"
          value={draft.priority}
          onChange={(event) => update("priority", event.target.value)}
        />
      </label>
      <label>
        assignee
        <input
          aria-label="assignee"
          value={draft.assignee}
          onChange={(event) => update("assignee", event.target.value)}
        />
      </label>
      <button type="submit">add</button>
      {Object.entries(errors).map(([field, message]) => (
        <p key={field} data-testid={`error-${field}`}>
          {message}
        </p>
      ))}
    </form>
  );
}
