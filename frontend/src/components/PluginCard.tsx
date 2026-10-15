import { Link } from "react-router-dom";
import type { PluginListItem } from "../types";

const CATEGORY_LABELS: Record<PluginListItem["category"], string> = {
  lsp: "LSP",
  mcp: "MCP",
  tool: "Tool",
  utility: "Utility",
  other: "Other",
};

export default function PluginCard({ plugin }: { plugin: PluginListItem }) {
  const badgeClass = `badge-${plugin.category}`;
  const categoryLabel = CATEGORY_LABELS[plugin.category] ?? plugin.category;

  return (
    <Link to={`/plugins/${plugin.slug}`} className="card" style={{ display: "block" }}>
      <div className="flex-between">
        <div>
          <h3>{plugin.name}</h3>
          <span className={`badge ${badgeClass}`}>{categoryLabel}</span>
        </div>
        {plugin.has_lsp_config && <span className="badge badge-lsp">LSP</span>}
      </div>
      <p className="text-sm mt-2 text-muted">{plugin.description}</p>
      {plugin.author && (
        <p className="text-sm mt-2">by {plugin.author}</p>
      )}
      {plugin.version && (
        <p className="text-sm mt-2">v{plugin.version}</p>
      )}
      {plugin.tags.length > 0 && (
        <div className="tag-list mt-2">
          {plugin.tags.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}
    </Link>
  );
}