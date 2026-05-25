import type { TableDetail, TableNodeData } from "../types/graph";

const FK_HINTS = new Set([
  "fk",
  "foreign",
  "reference",
  "references",
  "join",
  "relationship",
]);

const STOPWORDS = new Set([
  "a",
  "an",
  "the",
  "is",
  "are",
  "in",
  "on",
  "for",
  "to",
  "of",
  "with",
  "what",
  "which",
  "where",
  "how",
  "show",
  "find",
  "list",
  "table",
  "tables",
  "column",
  "columns",
  "key",
]);

const TOKEN_EXPANSIONS: Record<string, string[]> = {
  fk: ["foreign", "key", "reference"],
  foreign: ["fk", "reference"],
  pk: ["primary", "key"],
  user: ["customer", "auth"],
  customer: ["client", "user"],
  order: ["purchase", "sale"],
  product: ["item", "sku"],
  email: ["mail"],
  status: ["state"],
};

function tokenize(query: string): string[] {
  const raw = query.toLowerCase().match(/[a-z0-9_]+/g) ?? [];
  return raw.filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

function expandToken(token: string): string[] {
  const terms = new Set<string>([token]);
  for (const extra of TOKEN_EXPANSIONS[token] ?? []) {
    terms.add(extra);
  }
  for (const [key, extras] of Object.entries(TOKEN_EXPANSIONS)) {
    if (extras.includes(token)) {
      terms.add(key);
      extras.forEach((e) => terms.add(e));
    }
  }
  return [...terms];
}

function tokenMatches(text: string, token: string): boolean {
  const variants = expandToken(token);
  return variants.some((v) => text.includes(v));
}

function buildSearchBlob(data: TableNodeData): string {
  const parts: string[] = [
    data.label,
    data.domain ?? "",
  ];
  const table = data.table;
  if (!table) {
    return parts.join(" ").toLowerCase();
  }

  parts.push(table.name);
  const dm = table.django_model;
  if (dm) {
    parts.push(dm.app_label, dm.model_name, dm.verbose_name ?? "", dm.doc ?? "");
  }
  const biz = table.business;
  if (biz) {
    parts.push(biz.description ?? "", ...(biz.hints ?? []));
  }
  for (const col of table.columns) {
    parts.push(
      col.name,
      col.type_display,
      col.django_field ?? "",
      col.verbose_name ?? "",
      col.help_text ?? ""
    );
  }
  for (const fk of [...table.outgoing_fks, ...table.incoming_fks]) {
    parts.push(fk.from_table, fk.from_column, fk.to_table, fk.to_column);
  }
  return parts.join(" ").toLowerCase();
}

function parseSearchQuery(query: string): {
  content: string[];
  wantsFk: boolean;
} {
  const tokens = tokenize(query.trim());
  const wantsFk = tokens.some((t) => FK_HINTS.has(t));
  const content = tokens.filter((t) => !FK_HINTS.has(t));
  return { content, wantsFk };
}

/** True when query tokens match table metadata (columns, docs, FKs, business text). */
export function tableMatchesSearch(data: TableNodeData, query: string): boolean {
  const { content, wantsFk } = parseSearchQuery(query);
  if (!content.length && !wantsFk) {
    return true;
  }
  const blob = buildSearchBlob(data);
  if (wantsFk) {
    const hasFk =
      (data.table?.outgoing_fks.length ?? 0) > 0 ||
      (data.table?.incoming_fks.length ?? 0) > 0;
    if (!hasFk) {
      return false;
    }
    if (!content.length) {
      return true;
    }
  }
  return content.every((token) => tokenMatches(blob, token));
}
