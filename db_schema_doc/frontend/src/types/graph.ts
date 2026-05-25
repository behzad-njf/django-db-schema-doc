import type { Edge, Node } from "@xyflow/react";

export type ColumnDetail = {
  name: string;
  type_display: string;
  nullable: boolean;
  default: string | null;
  ordinal: number;
  is_primary_key: boolean;
  django_field?: string;
  verbose_name?: string;
  help_text?: string;
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

export type DjangoModelDetail = {
  app_label: string;
  model_name: string;
  verbose_name?: string;
  verbose_name_plural?: string;
  doc?: string;
};

export type BusinessDetail = {
  description?: string;
  sources?: string[];
  hints?: string[];
};

export type QueryExampleDetail = {
  kind: "sql" | "orm" | string;
  title: string;
  code: string;
  related_tables?: string[];
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
  django_model?: DjangoModelDetail;
  business?: BusinessDetail;
  query_examples?: QueryExampleDetail[];
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
