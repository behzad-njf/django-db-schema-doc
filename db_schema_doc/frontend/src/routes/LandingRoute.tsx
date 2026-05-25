import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import LandingPage from "../components/landing/LandingPage";
import { useGraph } from "../context/GraphContext";
import { useDarkMode } from "../hooks/useDarkMode";

export default function LandingRoute() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { dark, toggle: toggleDark } = useDarkMode();
  const graph = useGraph();

  const openFilePicker = () => fileInputRef.current?.click();

  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) {
      graph.loadFromFile(file, () => navigate("/erd"));
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        className="file-input-hidden"
        onChange={onFileChange}
      />
      <LandingPage
        onOpenFile={openFilePicker}
        error={graph.error}
        dark={dark}
        onToggleDark={toggleDark}
      />
    </>
  );
}
