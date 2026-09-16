import { ReactNode } from "react";

export interface PanelProps {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}

/**
 * A frame that knows nothing about what it frames.
 *
 * children is just a prop that happens to hold elements, so a wrapper composes by
 * accepting content rather than by inheriting from anything. React has no component
 * inheritance at all — composition is the only mechanism, which is why a slot like this
 * is the idiom rather than a base class.
 *
 * The named `actions` slot shows the same trick where more than one hole is needed.
 */
export function Panel({ title, actions, children }: PanelProps) {
  return (
    <section data-testid="panel">
      <header>
        <h2>{title}</h2>
        {actions}
      </header>
      <div data-testid="panel-body">{children}</div>
    </section>
  );
}
