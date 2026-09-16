export interface PlaceholderProps {
  label?: string;
}

/**
 * Shown while nothing is chosen.
 *
 * Deliberately trivial. The component-testing harness needs something inert to render:
 * exercising it through a component another test already covers would leave a failure
 * ambiguous between the harness and that component.
 */
export function Placeholder({ label = "nothing selected" }: PlaceholderProps) {
  return (
    <p data-testid="placeholder">
      <span>{label}</span>
    </p>
  );
}
