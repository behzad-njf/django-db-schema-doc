import {
  AUTHOR_NAME,
  ERD_WEBSITE_URL,
  GITHUB_REPO_LABEL,
  GITHUB_REPO_URL,
} from "../../constants";
import DatabaseBackground from "./DatabaseBackground";

type Props = {
  onOpenFile: () => void;
  error: string;
  dark: boolean;
  onToggleDark: () => void;
};

export default function LandingPage({
  onOpenFile,
  error,
  dark,
  onToggleDark,
}: Props) {
  return (
    <div className="landing">
      <DatabaseBackground />
      <button
        type="button"
        className="landing__theme"
        onClick={onToggleDark}
        aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      >
        {dark ? "☀ Light" : "☾ Dark"}
      </button>

      <main className="landing__main">
        <p className="landing__eyebrow">db-schema-doc</p>
        <h1 className="landing__title">Schema explorer</h1>
        <p className="landing__lead">
          Visualize your database — tables, foreign keys, and column
          details in one interactive diagram.
        </p>

        <button type="button" className="landing__cta" onClick={onOpenFile}>
          Choose a json graph file
        </button>

        {error && <p className="landing__error">{error}</p>}

        <ul className="landing__hints">
          <li>
            Generate <code>graph.json</code> with{" "}
            <code>python manage.py generate_erd -o schema-erd</code>
          </li>
          <li>Double-click a table for details · Esc to reset focus</li>
        </ul>
      </main>

      <footer className="landing__footer">
        <span>
          By <strong>{AUTHOR_NAME}</strong> · MIT
        </span>
        <a
          href={GITHUB_REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="landing__footer-link"
        >
          {GITHUB_REPO_LABEL}
        </a>
        <a
          href={ERD_WEBSITE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="landing__footer-link"
        >
          Website
        </a>
      </footer>
    </div>
  );
}
