"""REST API endpoints for the plugin marketplace."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plugin import (
    PaginatedResponse,
    Plugin,
    PluginCategory,
    PluginDetail,
    PluginSubmission,
    PluginSubmissionCreate,
    PluginSubmissionRead,
    PluginSubmissionReview,
    PluginStatus,
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
# =============================================================================
# Plugin Submission Endpoints
# =============================================================================


@router.post("/submissions", response_model=PluginSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: PluginSubmissionCreate,
    db: Session = Depends(get_db),
) -> PluginSubmissionRead:
    """Create a new plugin submission for review."""
    # Check if a plugin with the same source URL already exists
    existing = db.execute(select(Plugin).where(Plugin.source_url == str(payload.source_url))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A plugin with this source URL already exists (ID: {existing.id})",
        )

    # Check for pending submission with same source URL
    pending = db.execute(
        select(PluginSubmission).where(
            PluginSubmission.source_url == str(payload.source_url),
            PluginSubmission.status == "pending",
        )
    ).scalar_one_or_none()
    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending submission with this source URL already exists",
        )

    submission = PluginSubmission(
        submitter_name=payload.submitter_name,
        submitter_email=payload.submitter_email,
        source_url=str(payload.source_url),
        proposed_category=payload.proposed_category,
        proposed_config=payload.proposed_config,
        status="pending",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return PluginSubmissionRead.model_validate(submission)


@router.get("/submissions", response_model=list[PluginSubmissionRead])
def list_submissions(
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status (pending, approved, rejected)"),
    db: Session = Depends(get_db),
) -> list[PluginSubmissionRead]:
    """List all plugin submissions (admin view)."""
    stmt = select(PluginSubmission).order_by(PluginSubmission.created_at.desc())
    if status_filter:
        stmt = stmt.where(PluginSubmission.status == status_filter)
    submissions = db.execute(stmt).scalars().all()
    return [PluginSubmissionRead.model_validate(s) for s in submissions]


@router.patch("/submissions/{submission_id}/review", response_model=PluginSubmissionRead)
def review_submission(
    submission_id: int,
    payload: PluginSubmissionReview,
    db: Session = Depends(get_db),
) -> PluginSubmissionRead:
    """Review a plugin submission (approve or reject)."""
    submission = db.get(PluginSubmission, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )

    if submission.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission already {submission.status}",
        )

    submission.status = payload.status
    submission.reviewer_notes = payload.reviewer_notes
    submission.reviewed_at = datetime.now()

    # If approved, create the plugin from the submission
    if payload.status == "approved":
        # Extract plugin data from proposed_config or use defaults
        config = submission.proposed_config or {}
        plugin = Plugin(
            slug=config.get("slug", submission.source_url.rstrip("/").split("/")[-1].lower().replace("_", "-")),
            name=config.get("name", "Unnamed Plugin"),
            description=config.get("description", ""),
            category=submission.proposed_category,
            status=PluginStatus.PUBLISHED,
            author=config.get("author", submission.submitter_name),
            version=config.get("version", "1.0.0"),
            tags=config.get("tags", []),
            source_url=submission.source_url,
            plugin_config=config,
            lsp_servers=config.get("lspServers"),
        )
        db.add(plugin)
        db.flush()  # Get the plugin ID
        submission.plugin_id = plugin.id

    db.commit()
    db.refresh(submission)
    return PluginSubmissionRead.model_validate(submission)