from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.core.database import Base


class PluginCategory(str, PyEnum):
    LSP = "lsp"
    MCP = "mcp"
    TOOL = "tool"
    UTILITY = "utility"
    OTHER = "other"


class PluginStatus(str, PyEnum):
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)  # README content
    category = Column(Enum(PluginCategory), nullable=False, default=PluginCategory.OTHER, index=True)
    status = Column(Enum(PluginStatus), nullable=False, default=PluginStatus.PUBLISHED, index=True)

    # Source & installation
    source_url = Column(String(500), nullable=True)  # GitHub repo URL
    install_command = Column(String(500), nullable=True)  # e.g., "npm install -g @vue/language-server"
    registry_name = Column(String(200), nullable=True)  # e.g., "@vue/language-server"

    # Plugin configuration (JSON)
    plugin_config = Column(JSON, nullable=True)  # plugin.json content
    lsp_servers = Column(JSON, nullable=True)  # .lsp.json content - LSP server definitions

    # Metadata
    author = Column(String(200), nullable=True)
    author_email = Column(String(200), nullable=True)
    license = Column(String(100), nullable=True)
    version = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)  # List of strings for search filtering

    # Timestamps (UTC)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    submissions = relationship("PluginSubmission", back_populates="plugin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_plugins_category_status", "category", "status"),
        Index("ix_plugins_name_trgm", "name"),  # For search (would need pg_trgm in Postgres)
    )


class PluginSubmission(Base):
    __tablename__ = "plugin_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="SET NULL"), nullable=True, index=True)
    submitter_name = Column(String(200), nullable=False)
    submitter_email = Column(String(200), nullable=False)
    source_url = Column(String(500), nullable=False)
    proposed_category = Column(Enum(PluginCategory), nullable=False)
    proposed_config = Column(JSON, nullable=True)  # plugin.json / .lsp.json
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    plugin = relationship("Plugin", back_populates="submissions")


# =============================================================================
# Pydantic Schemas (API contracts)
# =============================================================================

class LSPServerConfig(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    transport: str = "stdio"
    extension_to_language: dict[str, str] = Field(default_factory=dict, alias="extensionToLanguage")
    initialization_options: dict = Field(default_factory=dict, alias="initializationOptions")
    env: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class PluginConfig(BaseModel):
    name: str
    version: str
    description: str
    author: Optional[str] = None
    repository: Optional[HttpUrl] = None
    license: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    lsp_servers: dict[str, LSPServerConfig] = Field(default_factory=dict, alias="lspServers")

    model_config = ConfigDict(populate_by_name=True)


class PluginBase(BaseModel):
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    long_description: Optional[str] = None
    category: PluginCategory = PluginCategory.OTHER
    source_url: Optional[HttpUrl] = None
    install_command: Optional[str] = None
    registry_name: Optional[str] = None
    plugin_config: Optional[dict] = None
    lsp_servers: Optional[dict] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    license: Optional[str] = None
    version: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class PluginCreate(PluginBase):
    pass


class PluginUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    long_description: Optional[str] = None
    category: Optional[PluginCategory] = None
    status: Optional[PluginStatus] = None
    source_url: Optional[HttpUrl] = None
    install_command: Optional[str] = None
    registry_name: Optional[str] = None
    plugin_config: Optional[PluginConfig] = None
    lsp_servers: Optional[dict[str, LSPServerConfig]] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    license: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[list[str]] = None


class PluginRead(PluginBase):
    id: int
    status: PluginStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PluginListItem(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    category: PluginCategory
    status: PluginStatus
    author: Optional[str] = None
    version: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    lsp_servers: Optional[dict] = Field(default=None, exclude=True)
    has_lsp_config: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _compute_lsp_flag(self) -> "PluginListItem":
        self.has_lsp_config = bool(self.lsp_servers)
        return self


class PluginDetail(PluginRead):
    plugin_config: Optional[dict] = None
    lsp_servers: Optional[dict] = None
    install_command: Optional[str] = None
    registry_name: Optional[str] = None
    source_url: Optional[HttpUrl] = None


class PaginatedResponse(BaseModel):
    items: list[PluginListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class PluginSubmissionCreate(BaseModel):
    submitter_name: str = Field(..., min_length=1, max_length=200)
    submitter_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    source_url: HttpUrl
    proposed_category: PluginCategory
    proposed_config: Optional[dict] = None


class PluginSubmissionRead(BaseModel):
    id: int
    plugin_id: Optional[int] = None
    submitter_name: str
    submitter_email: str
    source_url: HttpUrl
    proposed_category: PluginCategory
    proposed_config: Optional[dict] = None
    status: str
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PluginSubmissionReview(BaseModel):
    status: str = Field(..., pattern=r"^(approved|rejected)$")
    reviewer_notes: Optional[str] = None