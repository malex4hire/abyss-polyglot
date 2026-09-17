export interface HeadingProps {
  count: number;
  assignee: string;
}

/**
 * Markup as an expression.
 *
 * JSX is not a template language: it compiles to function calls, so every brace holds a
 * JavaScript expression and the whole thing is a value that can be returned, stored or
 * passed. The consequences are the small surprises: className rather than class,
 * camelCase attributes, and one root element or a fragment, because a function returns
 * one thing.
 */
export function Heading({ count, assignee }: HeadingProps) {
  const label = count === 1 ? "item" : "items";
  return (
    <>
      <h1 className="board-heading" data-testid="heading">
        {count} {label} for {assignee}
      </h1>
      <p data-testid="heading-note">{count > 5 && "busy week"}</p>
    </>
  );
}
