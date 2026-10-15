"""Tests for the plugin marketplace REST API."""

from __future__ import annotations

from fastapi import status


PLUGINS_URL = "/api/v1/plugins"


class TestListPlugins:
    def test_list_returns_paginated_response(self, client):
        resp = client.get(f"{PLUGINS_URL}?page_size=5")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] > 0
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] >= 1
        assert len(data["items"]) == 5

    def test_list_default_pagination(self, client):
        resp = client.get(PLUGINS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) <= 20

    def test_list_second_page(self, client):
        resp = client.get(f"{PLUGINS_URL}?page=2&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert len(data["items"]) == 5

    def test_list_page_clamped_to_one(self, client):
        resp = client.get(f"{PLUGINS_URL}?page=0&page_size=5")
        assert resp.status_code == 200
        assert resp.json()["page"] == 1

    def test_search_by_name(self, client):
        resp = client.get(f"{PLUGINS_URL}?search=vue&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Vue Language Server (Volar)"

    def test_search_case_insensitive(self, client):
        resp = client.get(f"{PLUGINS_URL}?search=VUE&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_search_no_match(self, client):
        resp = client.get(f"{PLUGINS_URL}?search=nonexistentplugin123&page_size=20")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_category_lsp(self, client):
        resp = client.get(f"{PLUGINS_URL}?category=lsp&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["category"] == "lsp" for item in data["items"])

    def test_filter_by_has_lsp(self, client):
        resp = client.get(f"{PLUGINS_URL}?has_lsp=true&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["has_lsp_config"] is True for item in data["items"])
        assert all(item["category"] == "lsp" for item in data["items"])

    def test_filter_by_has_lsp_false(self, client):
        resp = client.get(f"{PLUGINS_URL}?has_lsp=false&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["has_lsp_config"] is False for item in data["items"])

    def test_invalid_category_returns_400(self, client):
        resp = client.get(f"{PLUGINS_URL}?category=bogus&page_size=5")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_page_size_capped_at_max(self, client):
        resp = client.get(f"{PLUGINS_URL}?page_size=999")
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 100


class TestGetPluginDetail:
    def test_get_by_id(self, client):
        resp = client.get(f"{PLUGINS_URL}/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["slug"]
        assert data["name"]
        assert data["description"]
        assert "created_at" in data

    def test_get_by_slug(self, client):
        resp = client.get(f"{PLUGINS_URL}/by-slug/typescript-lsp")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "typescript-lsp"
        assert data["lsp_servers"] is not None

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get(f"{PLUGINS_URL}/99999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_get_nonexistent_slug_returns_404(self, client):
        resp = client.get(f"{PLUGINS_URL}/by-slug/nonexistent-slug-xyz")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_includes_install_command(self, client):
        resp = client.get(f"{PLUGINS_URL}/by-slug/vue-volar-lsp")
        assert resp.status_code == 200
        data = resp.json()
        assert data["install_command"] == "npm install -g @vue/language-server"
        assert data["source_url"] is not None


class TestLspConfigEndpoint:
    def test_get_lsp_config_success(self, client):
        resp = client.get(f"{PLUGINS_URL}/1/lsp-config")
        assert resp.status_code == 200
        config = resp.json()
        assert "lspServers" in config
        assert "vue" not in config["lspServers"]  # plugin 1 is TypeScript
        assert "typescript" in config["lspServers"]
        assert config["lspServers"]["typescript"]["command"] == "typescript-language-server"

    def test_get_lsp_config_vue_volar(self, client):
        """Issue #232: Vue/Volar LSP plugin config."""
        resp = client.get(f"{PLUGINS_URL}/12/lsp-config")
        assert resp.status_code == 200
        config = resp.json()
        assert "vue" in config["lspServers"]
        assert config["lspServers"]["vue"]["command"] == "vue-language-server"
        # The .lsp.json should include the tsdk path from init options.
        init_opts = config["lspServers"]["vue"].get("initializationOptions", {})
        assert init_opts.get("typescript", {}).get("tsdk") == "node_modules/typescript/lib"

    def test_get_lsp_config_no_lsp_returns_404(self, client):
        """Issue #379: non-LSP plugins should not have an LSP config."""
        # Plugin 13 is the GitHub MCP Server (no LSP config)
        resp = client.get(f"{PLUGINS_URL}/13/lsp-config")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_get_lsp_config_nonexistent_returns_404(self, client):
        resp = client.get(f"{PLUGINS_URL}/99999/lsp-config")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestSearchFiltering:
    def test_search_by_tag(self, client):
        resp = client.get(f"{PLUGINS_URL}?tag=typescript&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_by_author(self, client):
        resp = client.get(f"{PLUGINS_URL}?author=Microsoft&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert "Microsoft" in item["author"]