/** Type definitions mirroring the backend Pydantic schemas. */

export type PluginCategory = "lsp" | "mcp" | "tool" | "utility" | "other";

export type PluginStatus = "published" | "deprecated" | "archived";

export interface LspServerConfig {
  command: string;
  args?: string[];
  transport?: string;
  extensionToLanguage?: Record<string, string>;
  initializationOptions?: Record<string, unknown>;
  env?: Record<string, string>;
}

export interface PluginListItem {
  id: number;
  slug: string;
  name: string;
  description: string;
  category: PluginCategory;
  status: PluginStatus;
  author?: string | null;
  version?: string | null;
  tags: string[];
  has_lsp_config: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse {
  items: PluginListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PluginDetail {
  id: number;
  slug: string;
  name: string;
  description: string;
  long_description?: string | null;
  category: PluginCategory;
  status: PluginStatus;
  source_url?: string | null;
  install_command?: string | null;
  registry_name?: string | null;
  plugin_config?: Record<string, unknown> | null;
  lsp_servers?: Record<string, LspServerConfig> | null;
  author?: string | null;
  author_email?: string | null;
  license?: string | null;
  version?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  published_at?: string | null;
}

export interface LspConfig {
  $schema?: string;
  lspServers: Record<string, LspServerConfig>;
}

export interface PluginListParams {
  search?: string;
  category?: string;
  author?: string;
  tag?: string;
  has_lsp?: boolean;
  status?: string;
  page?: number;
  page_size?: number;
}
export interface PluginSubmissionCreate {
  submitter_name: string;
  submitter_email: string;
  source_url: string;
  proposed_category: PluginCategory;
  proposed_config?: Record<string, unknown>;
}

export interface PluginSubmissionRead {
  id: number;
  plugin_id: number | null;
  submitter_name: string;
  submitter_email: string;
  source_url: string;
  proposed_category: PluginCategory;
  proposed_config: Record<string, unknown> | null;
  status: "pending" | "approved" | "rejected";
  reviewer_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PluginSubmissionReview {
  status: "approved" | "rejected";
  reviewer_notes?: string;
}