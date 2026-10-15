# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] — 2026-10-15

### Added
- Plugin marketplace backend with FastAPI + SQLAlchemy + SQLite
- `GET /api/v1/plugins` with pagination, search, and category/author/tag/LSP filtering
- `GET /api/v1/plugins/{id}` and `GET /api/v1/plugins/by-slug/{slug}` detail endpoints
- `GET /api/v1/plugins/{id}/lsp-config` endpoint that generates `.lsp.json` from plugin LSP server definitions (fixes issue #379)
- LSP configuration engine (`app/services/lsp_config.py`) with deterministic generation, validation, and migration of marketplace-level configs to per-plugin files
- Seed data for 11 LSP plugins (issue #379) and Vue/Volar LSP plugin (issue #232)
- Health check endpoint (`GET /healthz`)
- React + TypeScript + Vite frontend with marketplace browse, plugin detail, and LSP config views
- Typed API client derived from backend routes
- Dockerfile and Compose configuration for backend, frontend, and Keycloak
- CI pipeline (GitHub Actions) with backend pytest, frontend build/test, Docker builds
- 42 backend tests covering API endpoints, LSP config engine, persistence, and boundary conditions