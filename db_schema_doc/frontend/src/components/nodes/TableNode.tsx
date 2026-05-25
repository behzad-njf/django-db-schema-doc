import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { TableNodeData } from "../../types/graph";

function TableNode({ data }: NodeProps<TableNodeData>) {
  const className = [
    "table-node",
    data.selected && "selected",
    data.dimmed && "dimmed",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <Handle type="target" position={Position.Top} />
      <div className="title">{data.label}</div>
      <div className="meta">
        {data.domain && <span>{data.domain} · </span>}
        {data.column_count ?? "?"} cols · FK {data.fk_out ?? 0} out /{" "}
        {data.fk_in ?? 0} in
      </div>
      <div className="meta hint">Double-click for details</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default memo(TableNode);
