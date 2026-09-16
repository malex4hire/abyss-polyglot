import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Placeholder } from "../components/Placeholder";

/**
 * Test the component the way a user meets it.
 *
 * Testing Library queries by accessible role and visible text rather than by class name
 * or component internals, so a test breaks when user-visible behaviour breaks and not
 * when the markup is refactored. That is the whole discipline: no shallow rendering, no
 * reaching into state, no asserting on props.
 *
 * userEvent drives real event sequences — a click is pointer-down, focus, pointer-up,
 * click — which is what catches a handler bound to the wrong event, or an element that
 * cannot actually be reached because something is covering it.
 *
 * Declared demo_only: a test harness is not on a served request path by construction.
 */
it("component-testing: queries by text, not by internals", async () => {
  const onOutside = vi.fn();
  render(
    <div onClick={onOutside}>
      <Placeholder label="pick an item" />
    </div>,
  );

  expect(screen.getByText("pick an item")).toBeInTheDocument();
  expect(screen.queryByText("nothing selected")).not.toBeInTheDocument();

  await userEvent.click(screen.getByText("pick an item"));

  expect(onOutside).toHaveBeenCalledOnce();
});
