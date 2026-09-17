import { useEffect, useRef } from "react";

/**
 * B4 on the React side: an effect that subscribes and returns its cleanup.
 *
 * The cleanup return is the mechanism. React calls it before the next run of the effect
 * and again at unmount, so the connection's lifetime is the component's lifetime, stated
 * in the same place the connection is opened, which is the property that makes it hard
 * to forget.
 *
 * The Angular counterpart attaches the same close to the stream itself, so the template
 * controls it. Both are correct; the difference is whether the lifetime belongs to the
 * component or to the stream.
 */
export function useChanges(base: string, onChange: () => void): void {
  // The callback is held in a ref and is NOT an effect dependency.
  //
  // It was a dependency, and its identity changes whenever the thing it closes over
  // changes, which here is the filter text. So every keystroke in the tag box tore the
  // connection down and opened a new one, and a change announced during the gap was gone
  // for good: no backend implements Last-Event-ID, so there is no replay. The Angular
  // side re-subscribes only on init and on a backend switch, which is the behaviour this
  // restores.
  //
  // The subscription's lifetime is now the BASE's lifetime, which is what it was always
  // meant to be. The cleanup return still states it in the same place the connection is
  // opened.
  const latest = useRef(onChange);
  latest.current = onChange;

  useEffect(() => {
    if (!base) return;
    const source = new EventSource(`${base}/events`);

    const handler = () => latest.current();
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
  }, [base]);
}
