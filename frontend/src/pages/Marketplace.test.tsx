import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Marketplace from "./Marketplace";
import * as api from "../api/client";
import type { PaginatedResponse } from "../types";

const MOCK_RESPONSE: PaginatedResponse = {
  items: [
    {
      id: 1,
      slug: "typescript-lsp",
      name: "TypeScript Language Server",
      description: "LSP for TypeScript",
      category: "lsp",
      status: "published",
      has_lsp_config: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      tags: ["typescript"],
    },
    {
      id: 2,
      slug: "vue-volar-lsp",
      name: "Vue Language Server (Volar)",
      description: "LSP for Vue",
      category: "lsp",
      status: "published",
      has_lsp_config: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      tags: ["vue"],
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

describe("Marketplace page", () => {
  beforeEach(() => {
    vi.spyOn(api, "fetchPlugins").mockResolvedValue(MOCK_RESPONSE);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state then plugin list", async () => {
    render(
      <MemoryRouter>
        <Marketplace />
      </MemoryRouter>
    );

    expect(screen.getByText("Loading plugins...")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("TypeScript Language Server")).toBeDefined();
    });
    expect(screen.getByText("Vue Language Server (Volar)")).toBeDefined();
    expect(screen.getByText("2 plugins found")).toBeDefined();
  });

  it("renders empty state when no plugins match", async () => {
    vi.spyOn(api, "fetchPlugins").mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    } as PaginatedResponse);

    render(
      <MemoryRouter>
        <Marketplace />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("No plugins found matching your criteria.")).toBeDefined();
    });
  });
});