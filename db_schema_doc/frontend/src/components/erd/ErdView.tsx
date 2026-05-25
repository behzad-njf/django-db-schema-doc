import ErdCanvas from "./ErdCanvas";
import TableDetailPanel from "../panel/TableDetailPanel";
import Toolbar from "../toolbar/Toolbar";
import type { useErdGraph } from "../../hooks/useErdGraph";

type GraphState = ReturnType<typeof useErdGraph>;

type Props = {
  graph: GraphState;
  dark: boolean;
  onToggleDark: () => void;
  onOpenFile: () => void;
  onGoHome: () => void;
};

export default function ErdView({
  graph,
  dark,
  onToggleDark,
  onOpenFile,
  onGoHome,
}: Props) {
  return (
    <div
      className={`app-layout${graph.detailTableId ? " app-layout--with-panel" : ""}`}
    >
      <Toolbar
        sourceLabel={graph.sourceLabel}
        meta={graph.meta}
        query={graph.query}
        onQueryChange={graph.setQuery}
        onOpenFile={onOpenFile}
        onGoHome={onGoHome}
        onClearFocus={graph.clearFocus}
        dark={dark}
        onToggleDark={onToggleDark}
        visibleCount={graph.visibleCount}
        tableCount={graph.tableCount}
      />

      {graph.error && (
        <div className="banner banner-warn">{graph.error}</div>
      )}

      <div className="workspace">
        <div className="flow-wrap">
          <ErdCanvas
            nodes={graph.nodes}
            edges={graph.edges}
            onNodesChange={graph.onNodesChange}
            onEdgesChange={graph.onEdgesChange}
            onNodeDragStart={graph.onNodeDragStart}
            onNodeDragStop={graph.onNodeDragStop}
            onNodeDoubleClick={graph.onNodeDoubleClick}
            onPaneClick={graph.onPaneClick}
          />
        </div>

        <TableDetailPanel
          tableId={graph.detailTableId}
          table={graph.selectedTable}
          summary={graph.selectedSummary}
          onClose={graph.closeDetailPanel}
        />
      </div>
    </div>
  );
}
