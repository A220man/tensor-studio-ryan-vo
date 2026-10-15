"""LSP plugin configuration engine.

Claude Code language-server plugins declare their servers inside
``marketplace.json`` via the ``lspServers`` key.  When a plugin is
installed only the plugin *source directory* is cached — the
``marketplace.json`` block is silently dropped, so every LSP plugin
installs with zero configured servers (issue #379).

This module is the deterministic engine that bridges that gap: it takes
a plugin's stored ``lsp_server`` definition and emits a valid,
self-contained ``.lsp.json`` configuration file that Claude Code
expects to find at the root of the cached plugin directory.

All functions are pure and offline — no network or LLM access is
required.
"""

from __future__ import annotations

import json
from typing import Any

from app.models.plugin import LSPServerConfig

#: Keys that Claude Code recognises at the top level of ``.lsp.json``.
LSP_JSON_SCHEMA_KEYS = frozenset({"$schema", "lspServers"})

#: Required keys for every LSP server entry.
REQUIRED_SERVER_KEYS = frozenset({"command"})

#: Default transport value per Claude Code plugins reference docs.
DEFAULT_TRANSPORT = "stdio"


class LSPConfigError(ValueError):
    """Raised when an LSP configuration fails validation."""


def generate_lsp_json(lsp_servers: dict[str, LSPServerConfig] | None) -> str:
    """Render a ``.lsp.json`` document from a plugin's server definitions.

    The output preserves field aliases (``extensionToLanguage``,
    ``initializationOptions``) so the generated file is directly
    consumable by Claude Code without further transformation.

    Args:
        lsp_servers: Server definitions keyed by language identifier
            (e.g. ``"typescript"``, ``"vue"``).  ``None`` or an empty
            dict yields a minimal empty-but-valid document.

    Returns:
        A pretty-printed JSON string suitable for writing to
        ``<plugin-dir>/.lsp.json``.
    """
    servers = lsp_servers or {}
    payload: dict[str, Any] = {"$schema": LSP_JSON_SCHEMA_URL}

    rendered: dict[str, Any] = {}
    for name, config in servers.items():
        entry = {
            "command": config.command,
            "args": config.args,
            "transport": config.transport,
            "extensionToLanguage": config.extension_to_language,
            "initializationOptions": config.initialization_options,
        }
        # Omit empty optional fields for a cleaner file.
        if not entry["args"]:
            del entry["args"]
        if not entry["extensionToLanguage"]:
            del entry["extensionToLanguage"]
        if not entry["initializationOptions"]:
            del entry["initializationOptions"]
        if entry["transport"] == DEFAULT_TRANSPORT and "transport" in entry:
            del entry["transport"]
        rendered[name] = entry

    payload["lspServers"] = rendered
    return json.dumps(payload, indent=2, ensure_ascii=False)


# Canonical JSON Schema URL referenced by the ``.lsp.json`` documents.
LSP_JSON_SCHEMA_URL = (
    "https://code.claude.com/schemas/lsp-config.json"
)


def validate_lsp_json(config_text: str) -> dict[str, Any]:
    """Parse and validate a raw ``.lsp.json`` document.

    Args:
        config_text: The file contents as a string.

    Returns:
        The parsed configuration dict.

    Raises:
        LSPConfigError: If the JSON is malformed or fails semantic
            validation (missing ``lspServers``, unknown top-level keys,
            server entries lacking a ``command``, etc.).
    """
    try:
        config = json.loads(config_text)
    except json.JSONDecodeError as exc:
        raise LSPConfigError(f"Invalid JSON: {exc.msg} at line {exc.lineno}") from exc

    if not isinstance(config, dict):
        raise LSPConfigError("Top-level value must be a JSON object")

    unknown = set(config) - LSP_JSON_SCHEMA_KEYS
    if unknown:
        raise LSPConfigError(f"Unknown top-level keys: {sorted(unknown)}")

    if "lspServers" not in config:
        raise LSPConfigError("Missing required key 'lspServers'")

    servers = config["lspServers"]
    if not isinstance(servers, dict):
        raise LSPConfigError("'lspServers' must be a JSON object")

    for name, server in servers.items():
        if not isinstance(server, dict):
            raise LSPConfigError(
                f"Server '{name}' must be a JSON object"
            )
        missing = REQUIRED_SERVER_KEYS - set(server)
        if missing:
            raise LSPConfigError(
                f"Server '{name}' missing required key(s): {sorted(missing)}"
            )

    return config



def generate_lsp_json_from_raw(raw_servers: dict[str, dict] | None) -> str:
    """Render a ``.lsp.json`` from a raw dict of server configs.

    Unlike :func:`generate_lsp_config_for_plugin`, this operates on the
    ``lsp_servers`` column directly — the per-plugin config storage that
    LSP plugins use (e.g. Vue/Volar from issue #232).

    Args:
        raw_servers: Dict keyed by language identifier whose values are
            raw server config dicts (aliases accepted).

    Returns:
        Pretty-printed ``.lsp.json`` content as a string.
    """
    if not raw_servers:
        return generate_lsp_json(None)
    servers: dict[str, LSPServerConfig] = {}
    for name, entry in raw_servers.items():
        servers[name] = LSPServerConfig.model_validate(entry)
    return generate_lsp_json(servers)


def generate_lsp_config_for_plugin(plugin_config: dict[str, Any] | None) -> str:
    """Build a ``.lsp.json`` from a raw ``plugin.json``-style dict.

    This mirrors the migration fix from issue #379's PR #378: it
    extracts the ``lspServers`` block from the plugin manifest and
    produces the per-plugin ``.lsp.json`` file that was previously
    being lost on install.

    Args:
        plugin_config: A dict matching the ``PluginConfig`` schema
            (i.e. containing ``lspServers``).

    Returns:
        Rendered ``.lsp.json`` content as a string.
    """
    if not plugin_config:
        return generate_lsp_json(None)

    raw_servers = plugin_config.get("lspServers", plugin_config.get("lsp_servers"))
    if not raw_servers:
        return generate_lsp_json(None)

    servers: dict[str, LSPServerConfig] = {}
    for name, entry in raw_servers.items():
        servers[name] = LSPServerConfig.model_validate(entry)

    return generate_lsp_json(servers)


def has_lsp_config(lsp_servers: dict[str, LSPServerConfig] | None) -> bool:
    """Return ``True`` when a plugin declares at least one LSP server."""
    return bool(lsp_servers)


def list_server_commands(lsp_servers: dict[str, LSPServerConfig] | None) -> list[str]:
    """Return the ordered list of LSP server commands for a plugin.

    Used for quick display in plugin listings and for verifying that an
    editor can invoke the server binary.
    """
    if not lsp_servers:
        return []
    return [config.command for config in lsp_servers.values()]