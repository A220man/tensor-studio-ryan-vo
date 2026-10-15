"""Marketplace query, search, and pagination service.

All search logic is deterministic and runs entirely on indexed SQLite
columns.  Text matching is case-insensitive substring across the
plugin name and description; tag filtering uses JSON containment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.plugin import (
    Plugin,
    PluginCategory,
    PluginListItem,
    PaginatedResponse,
)


@dataclass
class SearchFilters:
    """Parsed query-string filters for the plugin list endpoint."""

    search: str | None = None
    category: PluginCategory | None = None
    author: str | None = None
    tag: str | None = None
    has_lsp: bool | None = None
    status: str | None = None


def _search_clause(base: str) -> str:
    """Build a LIKE pattern for case-insensitive substring matching."""
    escaped = base.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.lower()}%"


def _to_bool(value: str | None) -> bool | None:
    """Coerce a string query param to Optional[bool]."""
    if value is None:
        return None
    return value.lower() in ("1", "true", "yes")


def _extract_filters(params: dict[str, str]) -> SearchFilters:
    """Convert raw query-string params into typed :class:`SearchFilters`."""
    category = params.get("category")
    return SearchFilters(
        search=params.get("search"),
        category=PluginCategory(category) if category else None,
        author=params.get("author"),
        tag=params.get("tag"),
        has_lsp=_to_bool(params.get("has_lsp")),
        status=params.get("status"),
    )


def build_query(filters: SearchFilters):
    """Construct a SQLAlchemy SELECT with filters applied."""
    stmt = select(Plugin)
    if filters.search:
        pattern = _search_clause(filters.search)
        stmt = stmt.where(
            func.lower(
                func.coalesce(Plugin.name, "")
                + " "
                + func.coalesce(Plugin.description, "")
            ).like(pattern)
        )
    if filters.category:
        stmt = stmt.where(Plugin.category == filters.category)
    if filters.author:
        stmt = stmt.where(
            func.lower(Plugin.author).like(_search_clause(filters.author))
        )
    if filters.tag:
        tag_pattern = _search_clause(filters.tag)
        stmt = stmt.where(Plugin.tags.like(f"%{tag_pattern}%"))
    if filters.has_lsp is True:
        stmt = stmt.where(Plugin.lsp_servers.is_not(None))
    elif filters.has_lsp is False:
        stmt = stmt.where(Plugin.lsp_servers.is_(None))
    if filters.status:
        stmt = stmt.where(
            func.lower(Plugin.status).like(_search_clause(filters.status))
        )
    return stmt


def _to_list_item(plugin: Plugin) -> PluginListItem:
    """Manually build a :class:`PluginListItem` from a SQLAlchemy row.

    The ``has_lsp_config`` flag is computed by the model validator from
    the ``lsp_servers`` column, which is not itself exposed in the API
    output.  Explicit construction avoids validator ordering issues with
    ``model_validate`` on ORM objects.
    """
    return PluginListItem(
        id=plugin.id,
        slug=plugin.slug,
        name=plugin.name,
        description=plugin.description,
        category=plugin.category,
        status=plugin.status,
        author=plugin.author,
        version=plugin.version,
        tags=plugin.tags or [],
        lsp_servers=plugin.lsp_servers,
        created_at=plugin.created_at,
        updated_at=plugin.updated_at,
    )


def paginate(
    db: Session,
    filters: SearchFilters,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """Return a paginated, filtered list of plugins.

    Args:
        db: SQLAlchemy session.
        filters: Parsed search/filter criteria.
        page: 1-based page number (clamped to >= 1).
        page_size: Items per page (clamped to 1..max_page_size).

    Returns:
        A :class:`PaginatedResponse` with items, counts, and page info.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, settings.max_page_size))
    offset = (page - 1) * page_size

    base = build_query(filters)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    total_pages = (total + page_size - 1) // page_size if total else 0

    rows = db.execute(
        base.order_by(Plugin.name.asc()).offset(offset).limit(page_size)
    ).scalars().all()

    items = [_to_list_item(row) for row in rows]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_plugin_detail(db: Session, plugin_id: int):
    """Fetch a single plugin with full detail or ``None``."""
    stmt = select(Plugin).where(Plugin.id == plugin_id)
    return db.execute(stmt).scalars().first()


def get_plugin_by_slug(db: Session, slug: str):
    """Fetch a single plugin by its URL slug or ``None``."""
    stmt = select(Plugin).where(Plugin.slug == slug)
    return db.execute(stmt).scalars().first()