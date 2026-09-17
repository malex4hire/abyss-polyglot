import { useEffect, useState } from "react";

/**
 * A value that survives re-renders, and the setter that changes it.
 *
 * useState returns the current value and a setter; calling the setter schedules a
 * re-render rather than mutating anything in place. Updates batch, so reading the state
 * variable straight after setting it gives the old value, which is why the functional
 * form is the safe one when the next value depends on the last.
 */
export function useSelectionCount(): [number, () => void] {
  const [count, setCount] = useState(0);
  const bump = () => setCount((current) => current + 1);
  return [count, bump];
}

/**
 * Synchronise with something outside React.
 *
 * An effect runs after render, and its cleanup runs before the next one and at unmount,
 * which is what makes subscriptions, timers and listeners safe. The dependency array
 * says when to resynchronise; omit it and the effect runs every render, give it an empty
 * one and it never resynchronises.
 *
 * Returning the cleanup is the part people skip, and it is the part that prevents the
 * leak.
 */
export function useDocumentTitle(title: string): void {
  useEffect(() => {
    const previous = document.title;
    document.title = title;
    return () => {
      document.title = previous;
    };
  }, [title]);
}
