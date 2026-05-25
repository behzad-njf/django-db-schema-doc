import type { Edge, Node } from "@xyflow/react";
import { neighborIds } from "./neighbors";
import type { TableNodeData } from "../types/graph";

export type FilterInput = {
  allNodes: Node<TableNodeData>[];
  allEdges: Edge[];
  currentNodes: Node<TableNodeData>[];
  query: string;
  focusId: string | null;
};

export type FilterResult = {
  nodes: Node<TableNodeData>[];
  edges: Edge[];
};

/**
 * Apply search + FK-neighbor focus while preserving user-dragged node positions.
 */
export function applyNodeFilter({
  allNodes,
  allEdges,
  currentNodes,
  query,
  focusId,
}: FilterInput): FilterResult {
  const lower = query.trim().toLowerCase();
  let visible = allNodes;

  if (lower) {
    visible = allNodes.filter((n) => {
      const label = String(n.data?.label || n.id).toLowerCase();
      const domain = String(n.data?.domain || "").toLowerCase();
      return label.includes(lower) || domain.includes(lower);
    });
  }

  const visibleIds = new Set(visible.map((n) => n.id));

  if (focusId) {
    const related = neighborIds(focusId, allEdges);
    visibleIds.forEach((id) => {
      if (!related.has(id)) visibleIds.delete(id);
    });
    related.forEach((id) => visibleIds.add(id));
  }

  const relatedToFocus = focusId ? neighborIds(focusId, allEdges) : null;
  const positionById = new Map(
    currentNodes.map((n) => [n.id, n.position] as const)
  );

  const nodes = allNodes.map((n) => ({
    ...n,
    position: positionById.get(n.id) ?? n.position,
    hidden: !visibleIds.has(n.id),
    data: {
      ...n.data,
      dimmed: Boolean(
        focusId && focusId !== n.id && relatedToFocus && !relatedToFocus.has(n.id)
      ),
      selected: focusId === n.id,
    },
  }));

  const edges = allEdges.map((e) => ({
    ...e,
    hidden: !visibleIds.has(e.source) || !visibleIds.has(e.target),
    animated: focusId != null && (e.source === focusId || e.target === focusId),
    style:
      focusId && (e.source === focusId || e.target === focusId)
        ? { stroke: "var(--accent)", strokeWidth: 2 }
        : undefined,
  }));

  return { nodes, edges };
}
