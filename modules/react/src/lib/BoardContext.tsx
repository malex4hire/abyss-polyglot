import { createContext, ReactNode, useContext } from "react";

export interface BoardSettings {
  apiBase: string;
  pageSize: number;
}

const BoardSettingsContext = createContext<BoardSettings | null>(null);

export function BoardSettingsProvider({
  value,
  children,
}: {
  value: BoardSettings;
  children: ReactNode;
}) {
  return (
    <BoardSettingsContext.Provider value={value}>
      {children}
    </BoardSettingsContext.Provider>
  );
}

/**
 * Read shared settings without threading them through every component between.
 *
 * Context solves prop drilling, not state management: the provider still owns the value,
 * and every consumer re-renders when it changes, which is why a fast-changing value
 * belongs somewhere else. Throwing when there is no provider turns a silent undefined
 * into an error naming the missing provider, which is the difference between a
 * five-second fix and an afternoon.
 *
 * Angular reaches the same place through hierarchical injectors, where a provider on a
 * component overrides one further up.
 */
export function useBoardSettings(): BoardSettings {
  const settings = useContext(BoardSettingsContext);
  if (settings === null) {
    throw new Error("useBoardSettings must be used inside a BoardSettingsProvider");
  }
  return settings;
}
