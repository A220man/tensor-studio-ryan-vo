# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

plugin-submission

## Roadmap

### marketplace-browse — Plugin Marketplace Browse & Search

Status: done

Acceptance:
- GET /api/v1/plugins returns paginated list of plugins with name, description, category, author
- GET /api/v1/plugins/{id} returns plugin detail with installation config, readme, version
- GET /api/v1/plugins?search=vue&q=typescript filters plugins by name/description/tags
- Frontend marketplace page lists plugins with search, pagination, category filter
- Plugin detail page shows install command, configuration, source link, readme

Implementation: `backend/app/main.py`, `backend/app/api/plugins.py`, `backend/app/services/marketplace.py`, `backend/app/services/lsp_config.py`, `backend/app/services/seed.py`, `backend/app/models/plugin.py`, `frontend/src/pages/Marketplace.tsx`, `frontend/src/pages/PluginDetail.tsx`, `frontend/src/components/PluginCard.tsx`, `frontend/src/components/SearchBar.tsx`, `frontend/src/components/Pagination.tsx`, `frontend/src/api/client.ts`

Tests: `backend/tests/test_plugins.py`, `backend/tests/test_lsp_config.py`, `frontend/src/api/client.test.ts`, `frontend/src/components/PluginCard.test.tsx`, `frontend/src/pages/Marketplace.test.tsx`

### lsp-plugin-support — LSP Plugin Configuration Support

Status: done

Acceptance:
- Plugin model includes lsp_servers field with command, args, initializationOptions
- GET /api/v1/plugins/{id}/lsp-config returns .lsp.json content
- Vue/Volar LSP plugin entry (issue #232)
- All 11 existing LSP plugins have valid lsp_servers config

Implementation: `backend/app/services/lsp_config.py`, `backend/app/services/seed.py`, `backend/app/models/plugin.py`

Tests: `backend/tests/test_lsp_config.py`

### plugin-submission — Plugin Submission & Review Workflow

Status: done

Acceptance:
- POST /api/v1/submissions creates plugin submission with validation
- GET /api/v1/submissions (admin) lists pending/approved/rejected
- PATCH /api/v1/submissions/{id}/review updates status with notes
- Frontend submission form with GitHub URL, category, plugin.json upload

Implementation: `backend/app/api/plugins.py`, `backend/app/models/plugin.py`, `frontend/src/pages/SubmitPlugin.tsx`, `frontend/src/api/client.ts`, `frontend/src/types.ts`, `frontend/src/App.tsx`, `frontend/src/pages/Marketplace.tsx`

Tests: `backend/tests/test_plugins.py::TestPluginSubmission`, `frontend/src/pages/SubmitPlugin.test.tsx`

### auth-oidc — OIDC Authentication with Keycloak

Status: planned

Acceptance:
- Login/logout via Keycloak authorization code flow with PKCE
- HttpOnly SameSite cookies for session, CSRF protection on writes
- Role-based access: viewer, submitter, admin
- Protected endpoints reject unauthenticated/invalid-role requests

### docker-ci — Docker Compose & CI Pipeline

Status: done

Acceptance:
- docker compose up starts backend, frontend, Keycloak, persistent volumes
- Healthchecks pass for all services
- CI runs backend pytest, frontend typecheck/build/test, Docker builds
- .env.example with all required configuration variables

Implementation: `compose.yaml`, `.github/workflows/ci.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example`

