import { MarkerType, type Edge, type Node } from "@xyflow/react";
import type { GraphPayload, ParsedGraph, TableNodeData } from "../types/graph";

export function parseGraphPayload(data: GraphPayload): ParsedGraph {
  const nodes = (data.nodes || []).map(
    (n) =>
      ({
        ...n,
        type: "table",
      }) as Node<TableNodeData>
  );

  const edges = (data.edges || []).map((e) => ({
    ...e,
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: false,
  })) as Edge[];

  const meta =
    [data.database_name, data.vendor].filter(Boolean).join(" · ") || "Schema ERD";

  return { nodes, edges, meta };
}
