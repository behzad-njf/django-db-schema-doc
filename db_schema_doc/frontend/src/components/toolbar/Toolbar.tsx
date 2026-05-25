type Props = {
  sourceLabel: string;
  meta: string;
  query: string;
  onQueryChange: (value: string) => void;
  onOpenFile: () => void;
  onGoHome: () => void;
  onClearFocus: () => void;
  dark: boolean;
  onToggleDark: () => void;
  visibleCount: number;
  tableCount: number;
};

export default function Toolbar({
  sourceLabel,
  meta,
  query,
  onQueryChange,
  onOpenFile,
  onGoHome,
  onClearFocus,
  dark,
  onToggleDark,
  visibleCount,
  tableCount,
}: Props) {
  return (
    <header className="erd-toolbar">
      <div className="erd-toolbar__brand">
        <span className="erd-toolbar__logo" aria-hidden>
          ◈
        </span>
        <div className="erd-toolbar__titles">
          <span className="erd-toolbar__name">Schema explorer</span>
          {meta && <span className="erd-toolbar__meta">{meta}</span>}
        </div>
        {sourceLabel && (
          <span className="erd-toolbar__file" title="Loaded graph file">
            {sourceLabel}
          </span>
        )}
      </div>

      <div className="erd-toolbar__search-wrap">
        <span className="erd-toolbar__search-icon" aria-hidden>
          ⌕
        </span>
        <input
          type="search"
          className="erd-toolbar__search"
          placeholder="Search tables or domain…"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
        />
      </div>

      <div className="erd-toolbar__actions">
        <span className="erd-toolbar__stat" title="Visible tables">
          {visibleCount}
          <span className="erd-toolbar__stat-sep">/</span>
          {tableCount}
        </span>
        <button
          type="button"
          className="erd-toolbar__btn"
          onClick={onGoHome}
          title="Back to home"
        >
          Home
        </button>
        <button
          type="button"
          className="erd-toolbar__btn"
          onClick={onClearFocus}
          title="Clear focus (Esc)"
        >
          Clear focus
        </button>
        <button
          type="button"
          className="erd-toolbar__btn erd-toolbar__btn--accent"
          onClick={onOpenFile}
          title="Load another graph.json"
        >
          Open file
        </button>
        <button
          type="button"
          className="erd-toolbar__btn erd-toolbar__btn--icon"
          onClick={onToggleDark}
          aria-label={dark ? "Light mode" : "Dark mode"}
          title={dark ? "Light mode" : "Dark mode"}
        >
          {dark ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
