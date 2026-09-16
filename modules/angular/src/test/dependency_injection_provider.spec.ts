import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { BOARD_SETTINGS, provideBoardSettings } from "../lib/providers";

it("dependency-injection-provider: maps a token to a recipe", () => {
  TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection(), provideBoardSettings({ pageSize: 0, apiBase: "" })],
  });

  const settings = TestBed.inject(BOARD_SETTINGS);
  expect(settings.pageSize).toBe(1);
});
