"""Seed data for the plugin marketplace.

Loads a deterministic set of plugins derived from the public issue
tracker of the reference marketplace (anthropics/claude-plugins-official).
The seed is idempotent: it only inserts when the table is empty.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.plugin import (
    LSPServerConfig,
    Plugin,
    PluginCategory,
    PluginStatus,
)

log = logging.getLogger("tensor_studio.seed")

# ---------------------------------------------------------------------------
# Plugin definitions — the 11 LSP plugins referenced in issue #379, plus
# the Vue/Volar plugin from issue #232 and several MCP/connectors.
# ---------------------------------------------------------------------------

_SEED_DATA = [
    # ---- LSP plugins (issue #379: all missing .lsp.json) ----
    {
        "slug": "typescript-lsp",
        "name": "TypeScript Language Server",
        "description": "TypeScript and JavaScript language server for Claude Code.",
        "category": "lsp",
        "author": "Sourcegraph",
        "version": "3.2.2",
        "install_command": "npm install -g typescript-language-server",
        "registry_name": "typescript-language-server",
        "tags": ["typescript", "javascript", "lsp"],
        "source_url": "https://github.com/typescript-eslint/typescript-language-server",
        "lsp_servers": {
            "typescript": {
                "command": "typescript-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".ts": "typescript", ".tsx": "typescript"},
                "initializationOptions": {"preferences": {"includeInlayParameterNameHints": "all"}},
            }
        },
    },
    {
        "slug": "pyright-lsp",
        "name": "Pyright Language Server",
        "description": "Fast Python type checker and language server.",
        "category": "lsp",
        "author": "Microsoft",
        "version": "1.1.391",
        "install_command": "npm install -g pyright",
        "registry_name": "pyright",
        "tags": ["python", "lsp", "type-checker"],
        "source_url": "https://github.com/microsoft/pyright",
        "lsp_servers": {
            "python": {
                "command": "pyright-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".py": "python"},
            }
        },
    },
    {
        "slug": "gopls-lsp",
        "name": "gopls Language Server",
        "description": "Official Go language server.",
        "category": "lsp",
        "author": "The Go Authors",
        "version": "0.17.1",
        "install_command": "go install golang.org/x/tools/gopls@latest",
        "registry_name": "gopls",
        "tags": ["go", "golang", "lsp"],
        "source_url": "https://github.com/golang/go",
        "lsp_servers": {
            "go": {
                "command": "gopls",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".go": "go"},
            }
        },
    },
    {
        "slug": "rust-analyzer-lsp",
        "name": "rust-analyzer",
        "description": "Fast Rust language server.",
        "category": "lsp",
        "author": "rust-analyzer",
        "version": "2025.1.0",
        "install_command": "rustup component add rust-analyzer",
        "registry_name": "rust-analyzer",
        "tags": ["rust", "lsp"],
        "source_url": "https://github.com/rust-lang/rust-analyzer",
        "lsp_servers": {
            "rust": {
                "command": "rust-analyzer",
                "transport": "stdio",
                "extensionToLanguage": {".rs": "rust"},
            }
        },
    },
    {
        "slug": "clangd-lsp",
        "name": "clangd",
        "description": "LLVM-based C/C++ language server.",
        "category": "lsp",
        "author": "LLVM",
        "version": "19.1.0",
        "install_command": "clangd --version  # or install via LLVM",
        "registry_name": "clangd",
        "tags": ["c", "cpp", "clang", "lsp"],
        "source_url": "https://github.com/llvm/llvm-project",
        "lsp_servers": {
            "cpp": {
                "command": "clangd",
                "args": ["--background-index"],
                "transport": "stdio",
                "extensionToLanguage": {".c": "cpp", ".cpp": "cpp", ".h": "cpp", ".hpp": "cpp"},
            }
        },
    },
    {
        "slug": "php-lsp",
        "name": "PHP Language Server",
        "description": "Language server for PHP using VS Code PHP Intelephense.",
        "category": "lsp",
        "author": "Microsoft",
        "version": "1.13.0",
        "install_command": "npm install -g php-language-server",
        "registry_name": "php-language-server",
        "tags": ["php", "lsp"],
        "source_url": "https://github.com/felixfbecker/php-language-server",
        "lsp_servers": {
            "php": {
                "command": "php-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".php": "php"},
            }
        },
    },
    {
        "slug": "swift-lsp",
        "name": "SourceKit-LSP",
        "description": "Swift and Objective-C language server based on SourceKitd.",
        "category": "lsp",
        "author": "Swift",
        "version": "6.0.0",
        "install_command": "swift package --disable-sandbox plugin install-source-kit-lsp",
        "registry_name": "sourcekit-lsp",
        "tags": ["swift", "objective-c", "lsp"],
        "source_url": "https://github.com/swiftlang/sourcekit-lsp",
        "lsp_servers": {
            "swift": {
                "command": "sourcekit-lsp",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".swift": "swift", ".m": "swift", ".mm": "swift"},
            }
        },
    },
    {
        "slug": "kotlin-lsp",
        "name": "Kotlin Language Server",
        "description": "Language server for Kotlin with IDE-like intelligence.",
        "category": "lsp",
        "author": "Kotlin",
        "version": "0.251.0",
        "install_command": "npm install -g kotlin-language-server",
        "registry_name": "kotlin-language-server",
        "tags": ["kotlin", "lsp"],
        "source_url": "https://github.com/fwcd/kotlin-language-server",
        "lsp_servers": {
            "kotlin": {
                "command": "kotlin-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".kt": "kotlin", ".kts": "kotlin"},
            }
        },
    },
    {
        "slug": "csharp-lsp",
        "name": "C# Language Server",
        "description": "OmniSharp-based C# language server.",
        "category": "lsp",
        "author": "OmniSharp",
        "version": "1.45.0",
        "install_command": "dotnet tool install -g csharp-ls",
        "registry_name": "csharp-ls",
        "tags": ["csharp", "dotnet", "lsp"],
        "source_url": "https://github.com/dotnet/roslyn",
        "lsp_servers": {
            "csharp": {
                "command": "csharpls",
                "args": ["-nologo"],
                "transport": "stdio",
                "extensionToLanguage": {".cs": "csharp", ".csx": "csharp"},
            }
        },
    },
    {
        "slug": "jdtls-lsp",
        "name": "Java Language Server (jdtls)",
        "description": "Eclipse JDT Language Server for Java.",
        "category": "lsp",
        "author": "Eclipse",
        "version": "1.33.0",
        "install_command": "Download from eclipse.org/jdtls/milestones",
        "registry_name": "jdtls",
        "tags": ["java", "lsp"],
        "source_url": "https://github.com/eclipse-jdtls/jdt.ls",
        "lsp_servers": {
            "java": {
                "command": "jdtls",
                "transport": "stdio",
                "extensionToLanguage": {".java": "java"},
            }
        },
    },
    {
        "slug": "lua-lsp",
        "name": "lua-language-server",
        "description": "Language server for Lua.",
        "category": "lsp",
        "author": "LuaLS",
        "version": "3.0.5",
        "install_command": "brew install lua-language-server  # or npm install -g lua-language-server",
        "registry_name": "lua-language-server",
        "tags": ["lua", "lsp"],
        "source_url": "https://github.com/LuaLS/lua-Language-Server",
        "lsp_servers": {
            "lua": {
                "command": "lua-language-server",
                "transport": "stdio",
                "extensionToLanguage": {".lua": "lua"},
            }
        },
    },
    # ---- Vue/Volar LSP plugin (issue #232) ----
    {
        "slug": "vue-volar-lsp",
        "name": "Vue Language Server (Volar)",
        "description": (
            "Vue.js LSP plugin using the Volar language server "
            "(@vue/language-server) enabling go-to-definition, hover, "
            "find references and TypeScript integration in .vue SFCs."
        ),
        "category": "lsp",
        "author": "Vue",
        "version": "3.0.0",
        "install_command": "npm install -g @vue/language-server",
        "registry_name": "@vue/language-server",
        "tags": ["vue", "typescript", "lsp", "frontend"],
        "source_url": "https://github.com/vuejs/language-tools",
        "lsp_servers": {
            "vue": {
                "command": "vue-language-server",
                "args": ["--stdio"],
                "transport": "stdio",
                "extensionToLanguage": {".vue": "vue"},
                "initializationOptions": {
                    "typescript": {"tsdk": "node_modules/typescript/lib"}
                },
            }
        },
    },
    # ---- MCP / Tool plugins ----
    {
        "slug": "github-mcp",
        "name": "GitHub MCP Server",
        "description": "Model Context Protocol server for GitHub API access.",
        "category": "mcp",
        "author": "GitHub",
        "version": "1.0.0",
        "install_command": "npx -y @modelcontextprotocol/server-github",
        "registry_name": "@modelcontextprotocol/server-github",
        "tags": ["github", "mcp", "git"],
        "source_url": "https://github.com/modelcontextprotocol/servers",
        "plugin_config": {"mcp": {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}},
    },
    {
        "slug": "slack-mcp",
        "name": "Slack MCP Server",
        "description": "Model Context Protocol server for Slack workspace access.",
        "category": "mcp",
        "author": "Slack",
        "version": "1.0.0",
        "install_command": "npm install -g @slack/mcp-server",
        "registry_name": "@slack/mcp-server",
        "tags": ["slack", "mcp"],
        "source_url": "https://github.com/slack-samples/bolt-mcp",
    },
    {
        "slug": "discord-connector",
        "name": "Discord Plugin",
        "description": "Discord connector for Claude Code — channels and messaging.",
        "category": "tool",
        "author": "Anthropic",
        "version": "1.2.0",
        "install_command": "npm install -g claude-plugin-discord",
        "registry_name": "claude-plugin-discord",
        "tags": ["discord", "messaging"],
        "source_url": "https://github.com/anthropics/claude-plugins-official",
    },
]


def _normalize_config(plugin_config: dict | None) -> dict | None:
    """Serialize nested config dicts to JSON-compatible form."""
    if plugin_config is None:
        return None
    return json.loads(json.dumps(plugin_config))


def seed_marketplace(db: Session | None = None) -> int:
    """Insert seed plugins if the plugins table is empty.

    Returns the number of plugins now stored.
    """
    if db is None:
        db = SessionLocal()
    try:
        existing = db.execute(select(Plugin)).scalars().all()
        if existing:
            return len(existing)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for entry in _SEED_DATA:
            lsp_servers = entry.get("lsp_servers")
            if lsp_servers:
                # Validate during seeding; store raw dict for JSON column.
                for _name, conf in lsp_servers.items():
                    LSPServerConfig.model_validate(conf)
            plugin_config = _normalize_config(entry.get("plugin_config"))

            plugin = Plugin(
                slug=entry["slug"],
                name=entry["name"],
                description=entry["description"],
                long_description=entry.get("long_description"),
                category=PluginCategory(entry["category"]),
                status=PluginStatus.PUBLISHED,
                source_url=entry.get("source_url"),
                install_command=entry.get("install_command"),
                registry_name=entry.get("registry_name"),
                author=entry.get("author"),
                author_email=entry.get("author_email"),
                license=entry.get("license"),
                version=entry.get("version"),
                tags=entry.get("tags", []),
                created_at=now,
                updated_at=now,
                published_at=now,
            )
            if plugin_config:
                plugin.plugin_config = plugin_config
            if lsp_servers:
                plugin.lsp_servers = lsp_servers
            db.add(plugin)

        db.commit()
        count = len(db.execute(select(Plugin)).scalars().all())
        log.info("Seeded marketplace with %d plugins", count)
        return count
    finally:
        if db is None:
            db.close()


__all__ = ["seed_marketplace"]