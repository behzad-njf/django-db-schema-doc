import type { Edge } from "@xyflow/react";

/** Tables connected by at least one foreign key to the given table. */
export function neighborIds(tableId: string, edges: Edge[]): Set<string> {
  const ids = new Set<string>([tableId]);
  for (const edge of edges) {
    if (edge.source === tableId) ids.add(edge.target);
    if (edge.target === tableId) ids.add(edge.source);
  }
  return ids;
}
