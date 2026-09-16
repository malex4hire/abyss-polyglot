/**
 * Angular's JIT compiler, and a test environment with no zone.
 *
 * Importing @angular/compiler is what lets TestBed compile a component's template at
 * runtime, which is the trade for not running the ahead-of-time plugin here.
 */
import "@angular/compiler";
import { getTestBed } from "@angular/core/testing";
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting,
} from "@angular/platform-browser-dynamic/testing";

getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting(),
);
