"""REST API endpoints for the plugin marketplace."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plugin import (
    PaginatedResponse,
    Plugin,
    PluginCategory,
    PluginDetail,
)
from app.services.lsp_config import generate_lsp_json_from_raw
from app.services.marketplace import (
    SearchFilters,
    get_plugin_by_slug,
    get_plugin_detail,
    paginate,
)

router = APIRouter(tags=["plugins"])


def _parse_category(value: str | None):
    if value is None:
        return None
    try:
        return PluginCategory(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {value}",
        )


@router.get("/plugins", response_model=PaginatedResponse)
def list_plugins(
    search: str | None = Query(default=None, description="Search by name or description"),
    category: str | None = Query(default=None, description="Filter by category"),
    author: str | None = Query(default=None, description="Filter by author"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    has_lsp: bool | None = Query(default=None, description="Filter to plugins with LSP config"),
    status: str | None = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=0, description="Page number (1-based, clamped to >=1)"),
    page_size: int = Query(default=20, ge=1, description="Items per page (clamped to max)"),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    """List plugins with pagination, search, and filtering."""
    filters = SearchFilters(
        search=search,
        category=_parse_category(category),
        author=author,
        tag=tag,
        has_lsp=has_lsp,
        status=status,
    )
    return paginate(db, filters, page, page_size)


@router.get("/plugins/{plugin_id}", response_model=PluginDetail)
def get_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginDetail:
    """Get a single plugin's full detail by ID."""
    plugin = get_plugin_detail(db, plugin_id)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )
    return PluginDetail.model_validate(plugin)


@router.get("/plugins/by-slug/{slug}", response_model=PluginDetail)
def get_plugin_by_slug_route(
    slug: str,
    db: Session = Depends(get_db),
) -> PluginDetail:
    """Get a single plugin's full detail by URL slug."""
    plugin = get_plugin_by_slug(db, slug)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{slug}' not found",
        )
    return PluginDetail.model_validate(plugin)


@router.get("/plugins/{plugin_id}/lsp-config", response_model=dict)
def get_lsp_config(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Generate and return the ``.lsp.json`` configuration for a plugin.

    This endpoint materialises the per-plugin LSP config that Claude
    Code expects at the root of the cached plugin directory, fixing the
    issue where marketplace-level ``lspServers`` definitions were lost
    on install (issue #379).
    """
    plugin = get_plugin_detail(db, plugin_id)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )
    if not plugin.lsp_servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin has no LSP server configuration",
        )
    config_text = generate_lsp_json_from_raw(plugin.lsp_servers)
    return json.loads(config_text)