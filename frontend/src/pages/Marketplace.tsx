import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchPlugins } from "../api/client";
import type { PaginatedResponse, PluginListItem } from "../types";
import PluginCard from "../components/PluginCard";
import SearchBar from "../components/SearchBar";
import Pagination from "../components/Pagination";

const CATEGORIES: { value: string; label: string }[] = [
  { value: "", label: "All Categories" },
  { value: "lsp", label: "LSP" },
  { value: "mcp", label: "MCP" },
  { value: "tool", label: "Tool" },
  { value: "utility", label: "Utility" },
  { value: "other", label: "Other" },
];

export default function Marketplace() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<PaginatedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const search = searchParams.get("search") ?? "";
  const category = searchParams.get("category") ?? "";
  const page = Number(searchParams.get("page") || "1");
  const page_size = Number(searchParams.get("page_size") || "20");
  const has_lsp = searchParams.get("has_lsp");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchPlugins({
          search: search || undefined,
          category: category || undefined,
          page,
          page_size,
          has_lsp: has_lsp === "true" ? true : has_lsp === "false" ? false : undefined,
        });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load plugins");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [search, category, page, page_size, has_lsp]);

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    next.set("page", "1");
    setSearchParams(next);
  };

  if (loading) {
    return <p className="text-muted">Loading plugins...</p>;
  }

  if (error) {
    return <p className="text-muted">Error: {error}</p>;
  }

  if (!data) {
    return <p className="text-muted">No data.</p>;
  }

  const items: PluginListItem[] = data.items;

  return (
    <div>
      <div className="flex-between mb-4">
        <SearchBar
          placeholder="Search by name, description, or tags..."
          initialValue={search}
          onSearch={(q) => updateParam("search", q)}
        />
        <div className="flex gap-2">
          <select
            className="input"
            style={{ maxWidth: "200px" }}
            value={category}
            onChange={(e) => updateParam("category", e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <a href="/submit" className="btn btn-sm">
            Submit Plugin
          </a>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="text-muted">No plugins found matching your criteria.</p>
      ) : (
        <>
          <p className="text-sm text-muted mt-2">
            {data.total} plugin{data.total !== 1 ? "s" : ""} found
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "1rem",
              marginTop: "1rem",
            }}
          >
            {items.map((plugin) => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))}
          </div>
          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            onPageChange={(p) =>
              setSearchParams({
                ...Object.fromEntries(searchParams),
                page: String(p),
              })
            }
          />
        </>
      )}
    </div>
  );
}