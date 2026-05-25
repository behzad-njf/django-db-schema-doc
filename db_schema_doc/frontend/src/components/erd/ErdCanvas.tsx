import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type OnEdgesChange,
  type OnNodesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import TableNode from "../nodes/TableNode";
import type { TableNodeData } from "../../types/graph";

const nodeTypes = { table: TableNode };

type Props = {
  nodes: Node<TableNodeData>[];
  edges: Edge[];
  onNodesChange: OnNodesChange<Node<TableNodeData>>;
  onEdgesChange: OnEdgesChange<Edge>;
  onNodeDragStart: (event: React.MouseEvent, node: Node<TableNodeData>) => void;
  onNodeDragStop: (event: React.MouseEvent, node: Node<TableNodeData>) => void;
  onNodeDoubleClick: (event: React.MouseEvent, node: Node<TableNodeData>) => void;
  onPaneClick: () => void;
};

export default function ErdCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onNodeDragStart,
  onNodeDragStop,
  onNodeDoubleClick,
  onPaneClick,
}: Props) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeDragStart={onNodeDragStart}
      onNodeDragStop={onNodeDragStop}
      onNodeDoubleClick={onNodeDoubleClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.05}
      maxZoom={2}
      nodesDraggable
      elementsSelectable
    >
      <Background />
      <Controls />
      <MiniMap zoomable pannable />
    </ReactFlow>
  );
}
