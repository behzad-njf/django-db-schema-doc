import type { TableDetail, TableNodeData } from "../../types/graph";

type Props = {
  tableId: string | null;
  table: TableDetail | null;
  summary: TableNodeData | null;
  onClose: () => void;
};

function FkRules({ onDelete, onUpdate }: { onDelete?: string; onUpdate?: string }) {
  if (!onDelete && !onUpdate) return null;
  const parts = [];
  if (onDelete) parts.push(`ON DELETE ${onDelete}`);
  if (onUpdate) parts.push(`ON UPDATE ${onUpdate}`);
  return <span className="fk-rules"> ({parts.join(", ")})</span>;
}

export default function TableDetailPanel({
  tableId,
  table,
  summary,
  onClose,
}: Props) {
  if (!tableId) return null;

  return (
    <aside className="detail-panel" aria-label="Table details">
      <header className="detail-panel__header">
        <div>
          <h2 className="detail-panel__title">{tableId}</h2>
          {summary?.domain && (
            <p className="detail-panel__subtitle">Domain: {summary.domain}</p>
          )}
        </div>
        <button
          type="button"
          className="detail-panel__close"
          onClick={onClose}
          aria-label="Close panel"
        >
          ×
        </button>
      </header>

      <div className="detail-panel__body">
        {!table ? (
          <p className="detail-panel__notice">
            Column details are not in this graph file. Regenerate with{" "}
            <code>python manage.py generate_erd</code> using the latest
            django-db-schema-doc.
          </p>
        ) : (
          <>
            <section className="detail-section">
              <h3>Overview</h3>
              <dl className="detail-dl">
                <dt>Primary key</dt>
                <dd>
                  {table.primary_key.length
                    ? table.primary_key.map((c) => (
                        <code key={c}>{c}</code>
                      ))
                    : "—"}
                </dd>
                {table.row_count != null && (
                  <>
                    <dt>Row count</dt>
                    <dd>{table.row_count.toLocaleString()}</dd>
                  </>
                )}
                <dt>Columns</dt>
                <dd>{table.columns.length}</dd>
              </dl>
            </section>

            <section className="detail-section">
              <h3>Columns</h3>
              <div className="detail-table-wrap">
                <table className="detail-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Null</th>
                      <th>Default</th>
                    </tr>
                  </thead>
                  <tbody>
                    {table.columns.map((col) => (
                      <tr key={col.name}>
                        <td>{col.ordinal}</td>
                        <td>
                          <code>
                            {col.name}
                            {col.is_primary_key ? " 🔑" : ""}
                          </code>
                        </td>
                        <td>{col.type_display}</td>
                        <td>{col.nullable ? "YES" : "NO"}</td>
                        <td>{col.default ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {table.outgoing_fks.length > 0 && (
              <section className="detail-section">
                <h3>References (outgoing)</h3>
                <ul className="detail-list">
                  {table.outgoing_fks.map((fk) => (
                    <li key={`${fk.from_column}-${fk.to_table}.${fk.to_column}`}>
                      <code>
                        {fk.from_column} → {fk.to_table}.{fk.to_column}
                      </code>
                      <FkRules
                        onDelete={fk.on_delete}
                        onUpdate={fk.on_update}
                      />
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {table.incoming_fks.length > 0 && (
              <section className="detail-section">
                <h3>Referenced by (incoming)</h3>
                <ul className="detail-list">
                  {table.incoming_fks.map((fk) => (
                    <li key={`${fk.from_table}.${fk.from_column}`}>
                      <code>
                        {fk.from_table}.{fk.from_column} → {table.name}.
                        {fk.to_column}
                      </code>
                      <FkRules
                        onDelete={fk.on_delete}
                        onUpdate={fk.on_update}
                      />
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {table.indexes.length > 0 && (
              <section className="detail-section">
                <h3>Indexes</h3>
                <ul className="detail-list">
                  {table.indexes.map((idx) => (
                    <li key={idx.name}>
                      <code>{idx.name}</code>
                      {idx.unique ? " (unique)" : ""}: {idx.columns.join(", ")}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {table.query_examples && table.query_examples.length > 0 && (
              <section className="detail-section">
                <h3>Query examples</h3>
                <ul className="detail-examples">
                  {table.query_examples.map((ex) => (
                    <li key={`${ex.kind}-${ex.title}`}>
                      <p className="detail-examples__title">
                        {ex.title}{" "}
                        <span className="detail-examples__badge">{ex.kind}</span>
                      </p>
                      <pre className="detail-examples__code">
                        <code>{ex.code}</code>
                      </pre>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
