# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint (2026-10-30)

### Verified
- All 54 backend tests pass (pytest)
- All 16 frontend tests pass (vitest)
- Frontend typecheck (tsc --noEmit) and production build (vite build) succeed
- API endpoints verified via test client:
  - GET /api/v1/plugins returns 15 seeded plugins with pagination, search, filtering
  - GET /api/v1/plugins/1/lsp-config returns valid .lsp.json with TypeScript LSP config

### Notes
- Docker compose not verified at runtime (no Docker daemon in this environment)
- Keycloak OIDC authentication (auth-oidc) remains planned

## [1.0.0] — 2026-10-22 (checkpoint)

### Added
- Plugin submission & review workflow (issue #984 reference)
  - `POST /api/v1/submissions` creates plugin submissions with validation (name, email, source URL, category, plugin.json config)
  - `GET /api/v1/submissions` lists all submissions with status filtering (pending/approved/rejected)
  - `PATCH /api/v1/submissions/{id}/review` approves or rejects submissions with reviewer notes
  - On approval, automatically creates a published plugin from the submission data
  - Duplicate detection: rejects submissions for existing source URLs or pending duplicates
- Frontend submission page (`/submit`) with form validation
  - Client-side validation for required fields, email format, URL format, JSON syntax
  - Accessible form with proper label associations
  - Success state with confirmation message
  - Error handling for API failures
- "Submit Plugin" link in marketplace header
- 12 new backend tests covering submission CRUD, validation, approval/rejection flow
- 7 new frontend tests covering form rendering, validation, submission, and error states
- Total: 54 backend tests, 16 frontend tests all passing

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
