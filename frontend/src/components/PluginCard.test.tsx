import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PluginCard from "./PluginCard";
import type { PluginListItem } from "../types";

const mockPlugin: PluginListItem = {
  id: 1,
  slug: "vue-volar-lsp",
  name: "Vue Language Server (Volar)",
  description: "LSP plugin for Vue.js",
  category: "lsp",
  status: "published",
  author: "Vue",
  version: "3.0.0",
  tags: ["vue", "typescript"],
  has_lsp_config: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("PluginCard", () => {
  it("renders plugin name, description, and LSP badge", () => {
    render(
      <MemoryRouter>
        <PluginCard plugin={mockPlugin} />
      </MemoryRouter>
    );

    expect(screen.getByText("Vue Language Server (Volar)")).toBeDefined();
    expect(screen.getByText("LSP plugin for Vue.js")).toBeDefined();
    expect(screen.getAllByText("LSP").length).toBeGreaterThan(0);
    expect(screen.getByText("by Vue")).toBeDefined();
    expect(screen.getByText("v3.0.0")).toBeDefined();
    expect(screen.getByText("vue")).toBeDefined();
  });

  it("renders link to plugin detail page", () => {
    render(
      <MemoryRouter>
        <PluginCard plugin={mockPlugin} />
      </MemoryRouter>
    );
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/plugins/vue-volar-lsp");
  });

  it("does not show LSP badge when has_lsp_config is false", () => {
    const noLspPlugin = { ...mockPlugin, has_lsp_config: false, category: "mcp" as const };
    render(
      <MemoryRouter>
        <PluginCard plugin={noLspPlugin} />
      </MemoryRouter>
    );
    const lspBadges = screen.queryAllByText("LSP");
    expect(lspBadges.length).toBe(0);
  });
});