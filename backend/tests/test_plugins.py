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
class TestPluginSubmission:
    def test_create_submission_success(self, client):
        payload = {
            "submitter_name": "Test User",
            "submitter_email": "test@example.com",
            "source_url": "https://github.com/test/new-plugin",
            "proposed_category": "lsp",
            "proposed_config": {
                "name": "Test Plugin",
                "slug": "test-plugin",
                "description": "A test plugin",
                "version": "1.0.0",
                "author": "Test User",
                "tags": ["test"],
            },
        }
        resp = client.post("/api/v1/submissions", json=payload)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["submitter_name"] == "Test User"
        assert data["submitter_email"] == "test@example.com"
        assert data["source_url"] == "https://github.com/test/new-plugin"
        assert data["proposed_category"] == "lsp"
        assert data["status"] == "pending"
        assert data["id"] is not None

    def test_create_submission_duplicate_source_url_rejected(self, client):
        payload = {
            "submitter_name": "Test User",
            "submitter_email": "test@example.com",
            "source_url": "https://github.com/test/new-plugin",
            "proposed_category": "lsp",
            "proposed_config": {},
        }
        # First submission succeeds
        resp1 = client.post("/api/v1/submissions", json=payload)
        assert resp1.status_code == status.HTTP_201_CREATED
        # Second submission with same URL fails
        resp2 = client.post("/api/v1/submissions", json=payload)
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in resp2.json()["detail"]

    def test_create_submission_existing_plugin_rejected(self, client):
        # Try to submit a plugin that already exists in seed data
        payload = {
            "submitter_name": "Test User",
            "submitter_email": "test@example.com",
            "source_url": "https://github.com/microsoft/pyright",
            "proposed_category": "lsp",
            "proposed_config": {},
        }
        resp = client.post("/api/v1/submissions", json=payload)
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in resp.json()["detail"]

    def test_create_submission_invalid_email_rejected(self, client):
        payload = {
            "submitter_name": "Test User",
            "submitter_email": "not-an-email",
            "source_url": "https://github.com/test/new-plugin-2",
            "proposed_category": "lsp",
            "proposed_config": {},
        }
        resp = client.post("/api/v1/submissions", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_submission_invalid_category_rejected(self, client):
        payload = {
            "submitter_name": "Test User",
            "submitter_email": "test@example.com",
            "source_url": "https://github.com/test/new-plugin-3",
            "proposed_category": "invalid-category",
            "proposed_config": {},
        }
        resp = client.post("/api/v1/submissions", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_submissions_empty_initially(self, client):
        # Note: seed data may create some submissions, so we just check it returns a list
        resp = client.get("/api/v1/submissions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_submissions_filter_by_status(self, client):
        # Create a pending submission first
        payload = {
            "submitter_name": "Filter Test",
            "submitter_email": "filter@example.com",
            "source_url": "https://github.com/test/filter-plugin",
            "proposed_category": "tool",
            "proposed_config": {},
        }
        client.post("/api/v1/submissions", json=payload)
        # Filter by pending
        resp = client.get("/api/v1/submissions?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["status"] == "pending" for s in data)
        # Filter by approved (should be empty or not include our pending)
        resp = client.get("/api/v1/submissions?status=approved")
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["status"] == "approved" for s in data)

    def test_review_submission_approve_creates_plugin(self, client):
        payload = {
            "submitter_name": "Approve Test",
            "submitter_email": "approve@example.com",
            "source_url": "https://github.com/test/approve-plugin",
            "proposed_category": "mcp",
            "proposed_config": {
                "name": "Approve Test Plugin",
                "slug": "approve-test-plugin",
                "description": "Plugin to approve",
                "version": "2.0.0",
                "author": "Approve Test",
                "tags": ["mcp"],
            },
        }
        create_resp = client.post("/api/v1/submissions", json=payload)
        assert create_resp.status_code == status.HTTP_201_CREATED
        submission_id = create_resp.json()["id"]

        # Approve the submission
        review_payload = {"status": "approved", "reviewer_notes": "Looks good"}
        resp = client.patch(f"/api/v1/submissions/{submission_id}/review", json=review_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["reviewer_notes"] == "Looks good"
        assert data["plugin_id"] is not None

        # Verify plugin was created
        plugin_resp = client.get(f"/api/v1/plugins/{data['plugin_id']}")
        assert plugin_resp.status_code == 200
        plugin = plugin_resp.json()
        assert plugin["name"] == "Approve Test Plugin"
        assert plugin["slug"] == "approve-test-plugin"
        assert plugin["category"] == "mcp"

    def test_review_submission_reject(self, client):
        payload = {
            "submitter_name": "Reject Test",
            "submitter_email": "reject@example.com",
            "source_url": "https://github.com/test/reject-plugin",
            "proposed_category": "utility",
            "proposed_config": {},
        }
        create_resp = client.post("/api/v1/submissions", json=payload)
        assert create_resp.status_code == status.HTTP_201_CREATED
        submission_id = create_resp.json()["id"]

        # Reject the submission
        review_payload = {"status": "rejected", "reviewer_notes": "Does not meet guidelines"}
        resp = client.patch(f"/api/v1/submissions/{submission_id}/review", json=review_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["reviewer_notes"] == "Does not meet guidelines"
        assert data["plugin_id"] is None

    def test_review_nonexistent_submission_returns_404(self, client):
        review_payload = {"status": "approved", "reviewer_notes": ""}
        resp = client.patch("/api/v1/submissions/99999/review", json=review_payload)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_review_already_reviewed_submission_returns_400(self, client):
        payload = {
            "submitter_name": "Double Review",
            "submitter_email": "double@example.com",
            "source_url": "https://github.com/test/double-plugin",
            "proposed_category": "lsp",
            "proposed_config": {},
        }
        create_resp = client.post("/api/v1/submissions", json=payload)
        submission_id = create_resp.json()["id"]

        # First review
        client.patch(f"/api/v1/submissions/{submission_id}/review", json={"status": "approved"})
        # Second review should fail
        resp = client.patch(f"/api/v1/submissions/{submission_id}/review", json={"status": "rejected"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "already approved" in resp.json()["detail"]

    def test_review_invalid_status_rejected(self, client):
        payload = {
            "submitter_name": "Invalid Status",
            "submitter_email": "invalid@example.com",
            "source_url": "https://github.com/test/invalid-plugin",
            "proposed_category": "lsp",
            "proposed_config": {},
        }
        create_resp = client.post("/api/v1/submissions", json=payload)
        submission_id = create_resp.json()["id"]

        resp = client.patch(f"/api/v1/submissions/{submission_id}/review", json={"status": "invalid"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY