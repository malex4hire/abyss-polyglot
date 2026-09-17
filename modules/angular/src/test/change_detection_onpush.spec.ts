import { expect, it } from "vitest";

import { TotalsComponent } from "../app/onpush.component";

it("change-detection-onpush: the component declares the OnPush strategy", () => {
  // render() produces the same string under either strategy, so asserting on its output
  // could not tell them apart — that assertion was vacuous, and a rival version under
  // the default strategy proved it. The strategy is not behaviour, it is a declaration
  // about how often Angular checks the view, and Angular records it on the compiled
  // component definition.
  const definition = (TotalsComponent as unknown as { ɵcmp: { onPush: boolean } }).ɵcmp;

  expect(definition).toBeDefined();
  expect(definition.onPush).toBe(true);
});
