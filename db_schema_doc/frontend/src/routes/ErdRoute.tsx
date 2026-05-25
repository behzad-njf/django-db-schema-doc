import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErdView from "../components/erd/ErdView";
import { useGraph } from "../context/GraphContext";
import { useDarkMode } from "../hooks/useDarkMode";

export default function ErdRoute() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { dark, toggle: toggleDark } = useDarkMode();
  const graph = useGraph();
  const [ready, setReady] = useState(false);
  const checkedRef = useRef(false);

  useEffect(() => {
    if (checkedRef.current) return;
    if (graph.hasGraph) {
      checkedRef.current = true;
      setReady(true);
      return;
    }
    checkedRef.current = true;
    if (graph.restoreSession()) {
      setReady(true);
      return;
    }
    navigate("/", { replace: true });
  }, [graph, navigate]);

  useEffect(() => {
    if (graph.hasGraph) setReady(true);
  }, [graph.hasGraph]);

  const openFilePicker = () => fileInputRef.current?.click();

  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) graph.loadFromFile(file);
  };

  const goHome = () => {
    graph.resetGraph();
    navigate("/");
  };

  if (!ready || !graph.hasGraph) {
    return null;
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        className="file-input-hidden"
        onChange={onFileChange}
      />
      <ErdView
        graph={graph}
        dark={dark}
        onToggleDark={toggleDark}
        onOpenFile={openFilePicker}
        onGoHome={goHome}
      />
    </>
  );
}
