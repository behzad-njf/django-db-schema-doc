import type { Edge, Node } from "@xyflow/react";

export type ColumnDetail = {
  name: string;
  type_display: string;
  nullable: boolean;
  default: string | null;
  ordinal: number;
  is_primary_key: boolean;
};

export type ForeignKeyDetail = {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  constraint_name?: string;
  on_delete?: string;
  on_update?: string;
};

export type IndexDetail = {
  name: string;
  columns: string[];
  unique: boolean;
};

export type TableDetail = {
  name: string;
  schema?: string;
  primary_key: string[];
  row_count: number | null;
  columns: ColumnDetail[];
  outgoing_fks: ForeignKeyDetail[];
  incoming_fks: ForeignKeyDetail[];
  indexes: IndexDetail[];
};

export type TableNodeData = {
  label: string;
  domain?: string;
  column_count?: number;
  fk_out?: number;
  fk_in?: number;
  table?: TableDetail;
  dimmed?: boolean;
  selected?: boolean;
};

export type GraphPayload = {
  schema_version?: number;
  database_name?: string;
  vendor?: string;
  nodes: Node<TableNodeData>[];
  edges: Edge[];
};

export type ParsedGraph = {
  nodes: Node<TableNodeData>[];
  edges: Edge[];
  meta: string;
};
