"""Response structure models for Amazing Marvin MCP."""

from dataclasses import dataclass
from typing import Any, NamedTuple


# Reference primitive using NamedTuple
class Reference(NamedTuple):
    """Primitive for referencing other objects"""

    item_id: str
    name: str | None = None


@dataclass
class CleanTask:
    """AI-friendly task object with reference primitives"""

    task_id: str
    title: str
    due_date: str | None = None
    priority: str | None = None
    scheduled_time: str | None = None
    completed: bool = False
    created_at: str | None = None
    note: str | None = None
    is_frogged: bool = False  # Special frog field!
    time_estimate: int | None = None
    time_block_section: str | None = None

    # Reference primitives
    project: Reference | None = None
    category: Reference | None = None
    labels: list[Reference] | None = None

    # Catch-all for unmapped fields
    other: dict[str, Any] | None = None


@dataclass
class CleanProject:
    """AI-friendly project object with reference primitives"""

    project_id: str
    title: str
    item_type: str = "project"
    description: str | None = None
    note: str | None = None

    # Reference primitives
    parent: Reference | None = None
    labels: list[Reference] | None = None

    # Catch-all
    other: dict[str, Any] | None = None


@dataclass
class ResponseMetadata:
    """Metadata about the data itself"""

    count: int
    start_date: str | None = None
    end_date: str | None = None
    source: str | None = None
    data_freshness: str = "real_time"
    filters_applied: list[str] | None = None


@dataclass
class ResponseSummary:
    """Human-readable insights"""

    text: str
    status: str
    action_completed: str | None = None


@dataclass
class ErrorDetails:
    """Structured error information"""

    error_type: str
    message: str
    user_message: str
    retry_suggested: bool = False


@dataclass
class ResponseDebug:
    """Technical execution details"""

    api_endpoint: str
    response_time_ms: int
    api_calls_made: int = 1
    cache_hit: bool = False
    warnings: list[str] | None = None  # API change warnings
    error: ErrorDetails | None = None  # Error details if failed


@dataclass
class StandardResponse:
    """Standard response structure for all tools"""

    data: Any
    metadata: ResponseMetadata
    summary: ResponseSummary
    debug: ResponseDebug | None
    success: bool
    api_version: str = "current"
    response_version: str = "1.0"
