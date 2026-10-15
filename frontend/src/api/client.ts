/**
 * Typed API client for the Tensor Studio marketplace backend.
 *
 * All functions return parsed JSON typed against the backend schemas.
 * Network errors propagate as rejected promises with a descriptive
 * ``message``.
 */

import type {
  LspConfig,
  PluginDetail,
  PluginListParams,
  PaginatedResponse,
} from "../types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";

let baseUrl = import.meta.env?.VITE_API_URL || DEFAULT_BASE_URL;

/** Override the base URL — used by tests and non-default deployments. */
export function setBaseUrl(url: string): void {
  baseUrl = url.replace(/\/+$/, "");
}

/** Build a query string from a params object, omitting undefined values. */
function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const parts = Object.entries(params).filter(([, v]) => v !== undefined);
  if (parts.length === 0) return "";
  const qs = parts
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return `?${qs}`;
}

/** Shared fetch wrapper with error handling. */
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${baseUrl}${path}`;
  const resp = await fetch(url, { ...init, headers: { Accept: "application/json", ...init?.headers } });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* not JSON */
    }
    throw new Error(`HTTP ${resp.status}: ${detail}`);
  }
  return (await resp.json()) as T;
}

/** Fetch a paginated, filtered list of plugins. */
export async function fetchPlugins(params: PluginListParams = {}): Promise<PaginatedResponse> {
  const query: Record<string, string | number | boolean | undefined> = {};
  if (params.search) query.search = params.search;
  if (params.category) query.category = params.category;
  if (params.author) query.author = params.author;
  if (params.tag) query.tag = params.tag;
  if (params.has_lsp !== undefined) query.has_lsp = params.has_lsp;
  if (params.status) query.status = params.status;
  if (params.page) query.page = params.page;
  if (params.page_size) query.page_size = params.page_size;
  return api<PaginatedResponse>(`/plugins${buildQuery(query)}`);
}

/** Fetch a single plugin by numeric ID. */
export async function fetchPlugin(id: number): Promise<PluginDetail> {
  return api<PluginDetail>(`/plugins/${id}`);
}

/** Fetch a single plugin by slug. */
export async function fetchPluginBySlug(slug: string): Promise<PluginDetail> {
  return api<PluginDetail>(`/plugins/by-slug/${slug}`);
}

/** Fetch the generated ``.lsp.json`` for a plugin. */
export async function fetchLspConfig(pluginId: number): Promise<LspConfig> {
  return api<LspConfig>(`/plugins/${pluginId}/lsp-config`);
}