"""Helper functions to convert existing tools to StandardResponse format."""

import logging
import time
from typing import Any

from .api import MarvinAPIClient
from .response_models import (
    ErrorDetails,
    ResponseDebug,
    ResponseMetadata,
    ResponseSummary,
    StandardResponse,
)
from .task_processor import process_tasks

logger = logging.getLogger(__name__)


def create_simple_response(
    data: Any,
    summary_text: str,
    api_endpoint: str,
    api_calls_made: int = 1,
    debug: bool = False,
    start_time: float | None = None,
) -> StandardResponse:
    """Create a simple StandardResponse for non-task data."""

    response_time = int((time.time() - start_time) * 1000) if start_time else 0

    # Determine count based on data type
    if isinstance(data, list):
        count = len(data)
    elif isinstance(data, dict):
        count = len(data) if data else 0
    else:
        count = 1 if data else 0

    return StandardResponse(
        data=data,
        metadata=ResponseMetadata(
            count=count,
            source=api_endpoint.replace("/", "").replace("_", " "),
            data_freshness="real_time",
        ),
        summary=ResponseSummary(
            text=summary_text, status="success", action_completed="data_retrieved"
        ),
        debug=ResponseDebug(
            api_endpoint=api_endpoint,
            response_time_ms=response_time,
            api_calls_made=api_calls_made,
            cache_hit=False,
        )
        if debug
        else None,
        success=True,
        api_version="current",
        response_version="1.0",
    )


def create_task_response(
    api_client: MarvinAPIClient,
    raw_tasks: list[dict],
    summary_text: str,
    api_endpoint: str,
    api_calls_made: int = 4,
    debug: bool = False,
    start_time: float | None = None,
) -> StandardResponse:
    """Create a StandardResponse for task data with full processing."""

    response_time = int((time.time() - start_time) * 1000) if start_time else 0

    # Process tasks with new structure
    clean_tasks, warnings = process_tasks(api_client, raw_tasks)

    return StandardResponse(
        data=clean_tasks,
        metadata=ResponseMetadata(
            count=len(clean_tasks),
            source=api_endpoint.replace("/", "").replace("_", " "),
            data_freshness="real_time",
        ),
        summary=ResponseSummary(
            text=summary_text, status="success", action_completed="tasks_retrieved"
        ),
        debug=ResponseDebug(
            api_endpoint=api_endpoint,
            response_time_ms=response_time,
            api_calls_made=api_calls_made,
            cache_hit=False,
            warnings=warnings if warnings else None,
        )
        if debug
        else None,
        success=True,
        api_version="current",
        response_version="1.0",
    )


def create_error_response(
    error: Exception,
    api_endpoint: str,
    debug: bool = False,
    start_time: float | None = None,
) -> StandardResponse:
    """Create a StandardResponse for errors."""

    response_time = int((time.time() - start_time) * 1000) if start_time else 0

    return StandardResponse(
        data=[],
        metadata=ResponseMetadata(
            count=0,
            source=api_endpoint.replace("/", "").replace("_", " "),
            data_freshness="unavailable",
        ),
        summary=ResponseSummary(
            text=f"Failed to retrieve data: {error!s}",
            status="error",
            action_completed="retrieval_failed",
        ),
        debug=ResponseDebug(
            api_endpoint=api_endpoint,
            response_time_ms=response_time,
            api_calls_made=0,
            cache_hit=False,
            error=ErrorDetails(
                error_type="api_error",
                message=str(error),
                user_message="Unable to connect to Amazing Marvin. Please check your connection and API key.",
                retry_suggested=True,
            ),
        )
        if debug
        else None,
        success=False,
        api_version="current",
        response_version="1.0",
    )
