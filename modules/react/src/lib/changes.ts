import { useEffect } from "react";

/**
 * B4 on the React side: an effect that subscribes and returns its cleanup.
 *
 * The cleanup return is the mechanism. React calls it before the next run of the effect
 * and again at unmount, so the connection's lifetime is the component's lifetime — stated
 * in the same place the connection is opened, which is the property that makes it hard
 * to forget.
 *
 * The Angular counterpart attaches the same close to the stream itself, so the template
 * controls it. Both are correct; the difference is whether the lifetime belongs to the
 * component or to the stream.
 */
export function useChanges(base: string, onChange: () => void): void {
  useEffect(() => {
    if (!base) return;
    const source = new EventSource(`${base}/events`);

    const handler = () => onChange();
    source.addEventListener("change", handler);

    // EventSource reconnects by itself, so an error is not terminal and closing here would
    // end a stream the browser is about to reopen.
    source.onerror = () => undefined;

    // The cleanup. Runs before the next effect and at unmount; without it a backend switch
    // leaves the previous connection open and the list updates from two streams.
    return () => {
      source.removeEventListener("change", handler);
      source.close();
    };
  }, [base, onChange]);
}
