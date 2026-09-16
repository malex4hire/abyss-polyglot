export interface EmptyStateProps {
  message?: string;
}

/**
 * A component is a function that takes props and returns what to render.
 *
 * That is the whole model. There is no lifecycle to implement and no base class to
 * extend — the function runs top to bottom on every render, and hooks give it memory
 * between runs. Rendering must stay pure: anything with an effect belongs in useEffect,
 * or it runs twice in development and at unpredictable times under concurrent rendering.
 *
 * Angular's counterpart is a class the framework instantiates and drives through
 * lifecycle callbacks. The difference shows in testing: this is called, not constructed.
 */
export function EmptyState({ message = "nothing selected" }: EmptyStateProps) {
  return <p data-testid="empty-state">{message}</p>;
}
