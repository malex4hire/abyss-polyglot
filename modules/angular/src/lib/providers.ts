import { InjectionToken, Provider } from "@angular/core";

export interface BoardSettings {
  pageSize: number;
  apiBase: string;
}

export const BOARD_SETTINGS = new InjectionToken<BoardSettings>("BOARD_SETTINGS");

/**
 * Teach the injector how to make something.
 *
 * A provider maps a token to a recipe: useValue for a constant, useClass for a type,
 * useFactory when construction needs work or other dependencies. An InjectionToken gives
 * an interface (which has no runtime existence) something the injector can key on.
 *
 * Providers are hierarchical: one declared on a component overrides the root for that
 * component and its children, which is how a test or a sub-tree substitutes an
 * implementation without touching the consumers. React's context is the closest
 * equivalent and carries values rather than construction recipes.
 */
export function provideBoardSettings(settings: BoardSettings): Provider {
  return {
    provide: BOARD_SETTINGS,
    useFactory: () => ({ ...settings, pageSize: Math.max(1, settings.pageSize) }),
  };
}
