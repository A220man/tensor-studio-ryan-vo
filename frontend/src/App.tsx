import { Routes, Route, Link } from "react-router-dom";
import Marketplace from "./pages/Marketplace";
import PluginDetail from "./pages/PluginDetail";

function App() {
  return (
    <div className="container mt-4">
      <header className="flex-between mb-4">
        <h1>
          <Link to="/">Tensor Studio</Link>
        </h1>
        <p className="text-sm text-muted">
          Claude Code Plugin Marketplace
        </p>
      </header>
      <Routes>
        <Route path="/" element={<Marketplace />} />
        <Route path="/plugins/:slug" element={<PluginDetail />} />
      </Routes>
    </div>
  );
}

export default App;