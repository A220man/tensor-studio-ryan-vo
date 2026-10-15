import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchPlugins, fetchPluginBySlug, fetchLspConfig, setBaseUrl } from "./client";

describe("API client", () => {
  beforeEach(() => {
    setBaseUrl("http://localhost:9999/api/v1");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchPlugins returns parsed paginated response", async () => {
    const mockData = {
      items: [{ id: 1, slug: "test", name: "Test", description: "desc", category: "lsp", status: "published", has_lsp_config: true, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" }],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    const mockJson = vi.fn().mockResolvedValue(mockData);
    const mockOk = { ok: true, json: mockJson } as unknown as Response;
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(mockOk);

    const result = await fetchPlugins({ search: "test", page: 1, page_size: 20 });
    expect(result.total).toBe(1);
    expect(result.items[0].name).toBe("Test");

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("search=test");
    expect(calledUrl).toContain("page=1");
  });

  it("fetchPluginBySlug fetches by slug", async () => {
    const mockData = { id: 1, slug: "test", name: "Test", description: "desc", category: "lsp", status: "published", tags: [], created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" };
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as unknown as Response);

    const result = await fetchPluginBySlug("test");
    expect(result.slug).toBe("test");
    expect(result.id).toBe(1);
  });

  it("fetchLspConfig returns parsed config", async () => {
    const mockConfig = {
      $schema: "https://example.com/schema.json",
      lspServers: {
        vue: {
          command: "vue-language-server",
          args: ["--stdio"],
          extensionToLanguage: { ".vue": "vue" },
        },
      },
    };
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockConfig),
    } as unknown as Response);

    const result = await fetchLspConfig(12);
    expect(result.lspServers.vue.command).toBe("vue-language-server");
  });

  it("throws on HTTP error with detail", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: "Plugin not found" }),
    } as unknown as Response);

    await expect(fetchPluginBySlug("missing")).rejects.toThrow("404");
  });
});