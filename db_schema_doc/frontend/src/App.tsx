import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import { GraphProvider } from "./context/GraphContext";
import ErdRoute from "./routes/ErdRoute";
import LandingRoute from "./routes/LandingRoute";

export default function App() {
  return (
    <HashRouter>
      <GraphProvider>
        <Routes>
          <Route path="/" element={<LandingRoute />} />
          <Route path="/erd" element={<ErdRoute />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </GraphProvider>
    </HashRouter>
  );
}
