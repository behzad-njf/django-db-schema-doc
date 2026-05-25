import { createContext, useContext, type ReactNode } from "react";
import { useErdGraph } from "../hooks/useErdGraph";

export type GraphContextValue = ReturnType<typeof useErdGraph>;

const GraphContext = createContext<GraphContextValue | null>(null);

export function GraphProvider({ children }: { children: ReactNode }) {
  const graph = useErdGraph();
  return (
    <GraphContext.Provider value={graph}>{children}</GraphContext.Provider>
  );
}

export function useGraph(): GraphContextValue {
  const ctx = useContext(GraphContext);
  if (!ctx) {
    throw new Error("useGraph must be used within GraphProvider");
  }
  return ctx;
}
