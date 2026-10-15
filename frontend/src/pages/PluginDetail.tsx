import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchPluginBySlug, fetchLspConfig } from "../api/client";
import type { PluginDetail, LspConfig } from "../types";

export default function PluginDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [plugin, setPlugin] = useState<PluginDetail | null>(null);
  const [lspConfig, setLspConfig] = useState<LspConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [lspLoading, setLspLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    fetchPluginBySlug(slug)
      .then(setPlugin)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [slug]);

  // Load LSP config if the plugin has LSP servers.
  useEffect(() => {
    if (plugin?.lsp_servers && Object.keys(plugin.lsp_servers).length > 0 && plugin?.id) {
      setLspLoading(true);
      fetchLspConfig(plugin.id)
        .then(setLspConfig)
        .catch(() => setLspConfig(null))
        .finally(() => setLspLoading(false));
    }
  }, [plugin]);

  if (loading) {
    return <p className="text-muted">Loading plugin...</p>;
  }

  if (error) {
    return <p className="text-muted">Error: {error}</p>;
  }

  if (!plugin) {
    return <p className="text-muted">Plugin not found.</p>;
  }

  return (
    <div>
      <Link to="/" className="btn mt-2">
        ← Back to Marketplace
      </Link>

      <div className="card mt-4">
        <div className="flex-between">
          <h1>{plugin.name}</h1>
          <span className={`badge badge-${plugin.category}`}>{plugin.category.toUpperCase()}</span>
        </div>

        <p className="mt-2">{plugin.description}</p>

        {plugin.long_description && (
          <div
            className="mt-4 text-sm"
            dangerouslySetInnerHTML={{ __html: plugin.long_description }}
          />
        )}

        <div className="mt-4">
          {plugin.version && <p><strong>Version:</strong> {plugin.version}</p>}
          {plugin.author && <p><strong>Author:</strong> {plugin.author}</p>}
          {plugin.license && <p><strong>License:</strong> {plugin.license}</p>}
          {plugin.registry_name && <p><strong>Registry:</strong> {plugin.registry_name}</p>}
        </div>

        {plugin.tags.length > 0 && (
          <div className="tag-list mt-4">
            {plugin.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        )}

        {plugin.install_command && (
          <div className="mt-4">
            <h3>Install Command</h3>
            <code style={{ background: "#0f172a", padding: "0.5rem", display: "block", borderRadius: "0.25rem" }}>
              {plugin.install_command}
            </code>
          </div>
        )}

        {plugin.source_url && (
          <div className="mt-4">
            <h3>Source</h3>
            <a href={plugin.source_url} target="_blank" rel="noopener noreferrer">
              {plugin.source_url}
            </a>
          </div>
        )}

        {plugin.lsp_servers && Object.keys(plugin.lsp_servers).length > 0 && (
          <div className="mt-4">
            <h3>LSP Servers</h3>
            <pre
              className="text-sm"
              style={{
                background: "#0f172a",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(plugin.lsp_servers, null, 2)}
            </pre>
          </div>
        )}

        {lspLoading && <p className="text-muted mt-4">Loading LSP config...</p>}

        {lspConfig && (
          <div className="mt-4">
            <h3>.lsp.json Configuration</h3>
            <pre
              className="text-sm"
              style={{
                background: "#0f172a",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(lspConfig, null, 2)}
            </pre>
            <p className="text-sm text-muted mt-2">
              Copy this content to <code>.lsp.json</code> in your plugin directory
              to fix issue #379.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}