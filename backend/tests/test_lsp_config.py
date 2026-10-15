"""Tests for the LSP configuration engine (issue #379 fix)."""

from __future__ import annotations

import json

import pytest

from app.services.lsp_config import (
    generate_lsp_json,
    generate_lsp_config_for_plugin,
    generate_lsp_json_from_raw,
    LSPConfigError,
    validate_lsp_json,
    has_lsp_config,
    list_server_commands,
)
from app.models.plugin import LSPServerConfig


class TestGenerateLspJson:
    def test_generate_with_servers(self):
        servers = {
            "typescript": LSPServerConfig(
                command="typescript-language-server",
                args=["--stdio"],
                extension_to_language={".ts": "typescript"},
                initialization_options={"preferences": {"includeInlayParameterNameHints": "all"}},
            )
        }
        result = generate_lsp_json(servers)
        config = json.loads(result)
        assert "lspServers" in config
        assert "typescript" in config["lspServers"]
        assert config["lspServers"]["typescript"]["command"] == "typescript-language-server"

    def test_generate_empty(self):
        result = generate_lsp_json(None)
        config = json.loads(result)
        assert "lspServers" in config
        assert config["lspServers"] == {}

    def test_generate_strips_default_transport(self):
        """transport='stdio' is the default and should be omitted."""
        servers = {
            "rust": LSPServerConfig(command="rust-analyzer", transport="stdio"),
        }
        result = generate_lsp_json(servers)
        config = json.loads(result)
        assert "transport" not in config["lspServers"]["rust"]

    def test_generate_keeps_non_default_transport(self):
        servers = {
            "go": LSPServerConfig(command="gopls", transport="tcp"),
        }
        result = generate_lsp_json(servers)
        config = json.loads(result)
        assert config["lspServers"]["go"]["transport"] == "tcp"


class TestGenerateFromRaw:
    def test_raw_dict_to_lsp_json(self):
        raw = {
            "vue": {
                "command": "vue-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".vue": "vue"},
                "initializationOptions": {
                    "typescript": {"tsdk": "node_modules/typescript/lib"}
                },
            }
        }
        result = generate_lsp_json_from_raw(raw)
        config = json.loads(result)
        assert "vue" in config["lspServers"]
        assert config["lspServers"]["vue"]["command"] == "vue-language-server"
        assert config["lspServers"]["vue"]["extensionToLanguage"] == {".vue": "vue"}
        assert config["lspServers"]["vue"]["initializationOptions"]["typescript"]["tsdk"] == "node_modules/typescript/lib"

    def test_raw_none_returns_empty(self):
        result = generate_lsp_json_from_raw(None)
        config = json.loads(result)
        assert config["lspServers"] == {}


class TestValidateLspJson:
    def test_valid_config(self):
        text = json.dumps({
            "$schema": "https://example.com/schema.json",
            "lspServers": {
                "typescript": {
                    "command": "typescript-language-server",
                    "args": ["--stdio"],
                    "transport": "stdio",
                }
            }
        })
        config = validate_lsp_json(text)
        assert "lspServers" in config

    def test_missing_lsp_servers(self):
        text = json.dumps({"$schema": "https://example.com/schema.json"})
        with pytest.raises(LSPConfigError, match="lspServers"):
            validate_lsp_json(text)

    def test_missing_command(self):
        text = json.dumps({
            "lspServers": {
                "typescript": {"args": ["--stdio"]}
            }
        })
        with pytest.raises(LSPConfigError, match="command"):
            validate_lsp_json(text)

    def test_invalid_json(self):
        with pytest.raises(LSPConfigError, match="Invalid JSON"):
            validate_lsp_json("{not valid json")

    def test_unknown_top_level_key(self):
        text = json.dumps({
            "lspServers": {"ts": {"command": "ts-ls"}},
            "unknownKey": True,
        })
        with pytest.raises(LSPConfigError, match="Unknown"):
            validate_lsp_json(text)

    def test_non_object_top_level(self):
        with pytest.raises(LSPConfigError, match="JSON object"):
            validate_lsp_json('"just a string"')


class TestPluginConfigExtraction:
    def test_extract_from_plugin_config(self):
        plugin_config = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "test",
            "lspServers": {
                "python": {
                    "command": "pyright-language-server",
                    "args": ["--stdio"],
                    "transport": "stdio",
                    "extensionToLanguage": {".py": "python"},
                }
            }
        }
        result = generate_lsp_config_for_plugin(plugin_config)
        config = json.loads(result)
        assert "python" in config["lspServers"]
        assert config["lspServers"]["python"]["command"] == "pyright-language-server"

    def test_plugin_config_none(self):
        result = generate_lsp_config_for_plugin(None)
        config = json.loads(result)
        assert config["lspServers"] == {}

    def test_plugin_config_no_lsp_servers(self):
        plugin_config = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "no LSP",
        }
        result = generate_lsp_config_for_plugin(plugin_config)
        config = json.loads(result)
        assert config["lspServers"] == {}


class TestHelperFunctions:
    def test_has_lsp_config_true(self):
        servers = {"ts": LSPServerConfig(command="ts-ls")}
        assert has_lsp_config(servers) is True

    def test_has_lsp_config_false(self):
        assert has_lsp_config(None) is False
        assert has_lsp_config({}) is False

    def test_list_server_commands(self):
        servers = {
            "typescript": LSPServerConfig(command="typescript-language-server"),
            "vue": LSPServerConfig(command="vue-language-server"),
        }
        commands = list_server_commands(servers)
        assert commands == ["typescript-language-server", "vue-language-server"]

    def test_list_server_commands_empty(self):
        assert list_server_commands(None) == []
        assert list_server_commands({}) == []