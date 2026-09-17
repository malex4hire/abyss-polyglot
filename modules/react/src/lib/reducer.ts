import { WorkItem } from "./types";

export interface BoardState {
  items: WorkItem[];
  selected: string | null;
}

export type BoardAction =
  | { type: "loaded"; items: WorkItem[] }
  | { type: "selected"; id: string }
  | { type: "cleared" };

/**
 * All state transitions for the board, in one place.
 *
 * A reducer is a pure function from state and action to state, so every way the board
 * can change is enumerated here rather than scattered across setState calls in
 * components. That is the trade against useState: more ceremony for one flag, and a
 * single readable answer to "how can this shape change" once there are several.
 *
 * Returning the same object when nothing changes matters: React bails out of the
 * re-render when the reference is unchanged.
 */
export function boardReducer(state: BoardState, action: BoardAction): BoardState {
  switch (action.type) {
    case "loaded":
      return { ...state, items: action.items };
    case "selected":
      return state.selected === action.id ? state : { ...state, selected: action.id };
    case "cleared":
      return state.selected === null ? state : { ...state, selected: null };
    default:
      return state;
  }
}
