import logging
import time
from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from .analytics import (
    get_completed_tasks as get_completed_tasks_impl,
)
from .analytics import (
    get_daily_productivity_overview as get_daily_productivity_overview_impl,
)
from .analytics import (
    get_productivity_summary_for_time_range as get_productivity_summary_for_time_range_impl,
)
from .api import create_api_client
from .projects import (
    create_project_with_tasks as create_project_impl,
)
from .projects import (
    get_project_overview as get_project_overview_impl,
)
from .response_models import StandardResponse
from .tasks import (
    batch_create_tasks as batch_create_tasks_impl,
)
from .tasks import (
    get_all_tasks_impl,
    get_child_tasks_recursive,
)
from .tool_converter import (
    create_error_response,
    create_simple_response,
    create_task_response,
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize MCP
mcp: FastMCP = FastMCP(name="amazing-marvin-mcp")


@mcp.tool()
async def get_tasks(debug: bool = False) -> StandardResponse:
    """Get today's scheduled tasks only.

    Use when you need only today's scheduled items without overdue or completed items.
    For comprehensive daily overview, use get_daily_productivity_overview() instead.
    For all tasks across projects, use get_all_tasks().
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        raw_tasks = api_client.get_tasks()

        return create_task_response(
            api_client=api_client,
            raw_tasks=raw_tasks,
            summary_text=f"Retrieved {len(raw_tasks)} scheduled tasks for today",
            api_endpoint="/todayItems",
            api_calls_made=4,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get tasks")
        return create_error_response(e, "/todayItems", debug, start_time)


@mcp.tool()
async def get_projects(debug: bool = False) -> StandardResponse:
    """Get all projects (categories with type 'project').

    Use when you need project list for organization or project selection.
    For detailed project analysis, use get_project_overview(project_id).
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        projects = api_client.get_projects()

        return create_simple_response(
            data=projects,
            summary_text=f"Retrieved {len(projects)} projects",
            api_endpoint="/categories",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get projects")
        return create_error_response(e, "/categories", debug, start_time)


@mcp.tool()
async def get_categories(debug: bool = False) -> StandardResponse:
    """Get categories from Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        categories = api_client.get_categories()

        return create_simple_response(
            data=categories,
            summary_text=f"Retrieved {len(categories)} categories",
            api_endpoint="/categories",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get categories")
        return create_error_response(e, "/categories", debug, start_time)


@mcp.tool()
async def get_due_items(debug: bool = False) -> StandardResponse:
    """Get overdue and due tasks only (past due date).

    Use when you need to focus specifically on urgent/overdue items.
    For complete daily view including today's tasks, use get_daily_productivity_overview().
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        due_items = api_client.get_due_items()

        return create_simple_response(
            data={"due_items": due_items},
            summary_text=f"Retrieved {len(due_items)} overdue/due items",
            api_endpoint="/dueItems",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get due items")
        return create_error_response(e, "/dueItems", debug, start_time)


@mcp.tool()
async def get_child_tasks(
    parent_id: str, recursive: bool = False, debug: bool = False
) -> StandardResponse:
    """Get child tasks of a specific parent task or project (experimental).

    Use when you need to see subtasks within a project or parent task.
    Returns both tasks and sub-projects. Set recursive=True for deep hierarchy.

    Args:
        parent_id: ID of the parent task or project
        recursive: If True, recursively get all descendants (can be expensive)

    Note: This is an experimental endpoint and may not work for all parent types.
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        if recursive:
            result = get_child_tasks_recursive(api_client, parent_id)
            api_calls = result.get("api_calls_made", 3)  # Estimate for recursive calls
        else:
            children = api_client.get_children(parent_id)
            # Categorize non-recursive results for consistency
            tasks = [item for item in children if item.get("type") != "project"]
            projects = [item for item in children if item.get("type") == "project"]

            result = {
                "parent_id": parent_id,
                "total_children": len(children),
                "tasks": tasks,
                "projects": projects,
                "task_count": len(tasks),
                "project_count": len(projects),
                "all_children": children,
                "recursive": False,
            }
            api_calls = 1

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved {result.get('total_children', 0)} child items for parent {parent_id}",
            api_endpoint="/children",
            api_calls_made=api_calls,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get child tasks for %s", parent_id)
        return create_error_response(e, "/children", debug, start_time)


@mcp.tool()
async def get_all_tasks(
    label: str | None = None, debug: bool = False
) -> StandardResponse:
    """Get all tasks across all projects with optional label filtering (comprehensive search).

    Use when you need to search/filter across your entire task system.
    For daily focus, use get_daily_productivity_overview() instead.

    Args:
        label: Optional label name to filter by. If None, returns all tasks.

    Note: This is a heavy operation that recursively searches all projects.
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = get_all_tasks_impl(api_client, label)

        # Estimate API calls based on typical project count
        estimated_api_calls = result.get("api_calls_made", 5)

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved {result.get('total_tasks', 0)} tasks across all projects"
            + (f" with label '{label}'" if label else ""),
            api_endpoint="/categories + /children",
            api_calls_made=estimated_api_calls,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get all tasks")
        return create_error_response(e, "/categories + /children", debug, start_time)


@mcp.tool()
async def get_labels(debug: bool = False) -> StandardResponse:
    """Get all labels from Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        labels = api_client.get_labels()

        return create_simple_response(
            data={"labels": labels},
            summary_text=f"Retrieved {len(labels)} labels",
            api_endpoint="/labels",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get labels")
        return create_error_response(e, "/labels", debug, start_time)


@mcp.tool()
async def get_goals(debug: bool = False) -> StandardResponse:
    """Get all goals from Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        goals = api_client.get_goals()

        return create_simple_response(
            data={"goals": goals},
            summary_text=f"Retrieved {len(goals)} goals",
            api_endpoint="/goals",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get goals")
        return create_error_response(e, "/goals", debug, start_time)


@mcp.tool()
async def get_account_info(debug: bool = False) -> StandardResponse:
    """Get account information from Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        account = api_client.get_account_info()

        return create_simple_response(
            data={"account": account},
            summary_text="Retrieved account information",
            api_endpoint="/me",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get account info")
        return create_error_response(e, "/me", debug, start_time)


@mcp.tool()
async def get_currently_tracked_item(debug: bool = False) -> StandardResponse:
    """Get currently tracked item from Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        tracked_item = api_client.get_currently_tracked_item()

        is_tracking = tracked_item and "message" not in tracked_item

        return create_simple_response(
            data={"tracked_item": tracked_item},
            summary_text="Currently tracking a task"
            if is_tracking
            else "No task currently being tracked",
            api_endpoint="/me/currentlyTrackedItem",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get currently tracked item")
        return create_error_response(e, "/me/currentlyTrackedItem", debug, start_time)


@mcp.tool()
async def create_task(
    title: str,
    project_id: str | None = None,
    category_id: str | None = None,
    due_date: str | None = None,
    note: str | None = None,
    debug: bool = False,
) -> StandardResponse:
    """Create a new task in Amazing Marvin.

    Args:
        title: Task title (required)
        project_id: Optional project ID to assign task to
        category_id: Optional category ID for organization
        due_date: Optional due date in YYYY-MM-DD format
        note: Optional task notes/description

    For creating multiple tasks, use batch_create_tasks() instead.
    For creating a project with tasks, use create_project_with_tasks().
    """
    start_time = time.time()
    try:
        api_client = create_api_client()

        task_data = {"title": title}
        if project_id:
            task_data["parentId"] = project_id
        if category_id:
            task_data["categoryId"] = category_id
        if due_date:
            task_data["dueDate"] = due_date
        if note:
            task_data["note"] = note

        created_task = api_client.create_task(task_data)

        return create_simple_response(
            data={"created_task": created_task},
            summary_text=f"Created task: {title}",
            api_endpoint="/addTask",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to create task '%s'", title)
        return create_error_response(e, "/addTask", debug, start_time)


@mcp.tool()
async def mark_task_done(
    item_id: str, timezone_offset: int = 0, debug: bool = False
) -> StandardResponse:
    """Mark a task as completed in Amazing Marvin.

    Args:
        item_id: Task ID to mark as done
        timezone_offset: Timezone offset in minutes from UTC (e.g., -480 for PST)

    For completing multiple tasks, use batch_mark_done(task_ids) instead.
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        completed_task = api_client.mark_task_done(item_id, timezone_offset)

        return create_simple_response(
            data={"completed_task": completed_task},
            summary_text=f"Marked task {item_id} as completed",
            api_endpoint="/markDone",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to mark task %s as done", item_id)
        return create_error_response(e, "/markDone", debug, start_time)


@mcp.tool()
async def test_api_connection(debug: bool = False) -> StandardResponse:  # noqa: PT028
    """Test the API connection and credentials.

    Use when troubleshooting connection issues or verifying API setup.
    Returns "OK" if successful or error details if failed.
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        status = api_client.test_api_connection()

        return create_simple_response(
            data={"status": status},
            summary_text=f"API connection test: {status}",
            api_endpoint="/me",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to test API connection")
        return create_error_response(e, "/me", debug, start_time)


@mcp.tool()
async def start_time_tracking(task_id: str, debug: bool = False) -> StandardResponse:
    """Start time tracking for a specific task.

    Use when beginning focused work on a task to measure time spent.
    Check current tracking status with get_currently_tracked_item() or time_tracking_summary().
    Stop tracking with stop_time_tracking(task_id).
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        tracking = api_client.start_time_tracking(task_id)

        return create_simple_response(
            data={"tracking": tracking},
            summary_text=f"Started time tracking for task {task_id}",
            api_endpoint="/startTimeTracking",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to start time tracking for task %s", task_id)
        return create_error_response(e, "/startTimeTracking", debug, start_time)


@mcp.tool()
async def stop_time_tracking(task_id: str, debug: bool = False) -> StandardResponse:
    """Stop time tracking for a specific task"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        tracking = api_client.stop_time_tracking(task_id)

        return create_simple_response(
            data={"tracking": tracking},
            summary_text=f"Stopped time tracking for task {task_id}",
            api_endpoint="/stopTimeTracking",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to stop time tracking for task %s", task_id)
        return create_error_response(e, "/stopTimeTracking", debug, start_time)


@mcp.tool()
async def get_time_tracks(task_ids: list[str], debug: bool = False) -> StandardResponse:
    """Get time tracking data for specific tasks"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        time_tracks = api_client.get_time_tracks(task_ids)

        return create_simple_response(
            data={"time_tracks": time_tracks},
            summary_text=f"Retrieved time tracking data for {len(task_ids)} tasks",
            api_endpoint="/timeTracks",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get time tracks")
        return create_error_response(e, "/timeTracks", debug, start_time)


@mcp.tool()
async def claim_reward_points(
    points: int, item_id: str, date: str, debug: bool = False
) -> StandardResponse:
    """Claim reward points for completing a task"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        reward = api_client.claim_reward_points(points, item_id, date)

        return create_simple_response(
            data={"reward": reward},
            summary_text=f"Claimed {points} reward points for task {item_id}",
            api_endpoint="/rewardPoints",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to claim reward points")
        return create_error_response(e, "/rewardPoints", debug, start_time)


@mcp.tool()
async def get_kudos_info(debug: bool = False) -> StandardResponse:
    """Get kudos and achievement information"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        kudos = api_client.get_kudos_info()

        return create_simple_response(
            data={"kudos": kudos},
            summary_text="Retrieved kudos and achievement information",
            api_endpoint="/me/kudos",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get kudos info")
        return create_error_response(e, "/me/kudos", debug, start_time)


@mcp.tool()
async def create_project(
    title: str, project_type: str = "project", debug: bool = False
) -> StandardResponse:
    """Create a new project in Amazing Marvin"""
    start_time = time.time()
    try:
        api_client = create_api_client()

        project_data = {"title": title, "type": project_type}
        created_project = api_client.create_project(project_data)

        return create_simple_response(
            data={"created_project": created_project},
            summary_text=f"Created project: {title}",
            api_endpoint="/addCategory",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to create project '%s'", title)
        return create_error_response(e, "/addCategory", debug, start_time)


@mcp.tool()
async def create_project_with_tasks(
    project_title: str,
    task_titles: list[str],
    project_type: str = "project",
    debug: bool = False,
) -> StandardResponse:
    """Create a project with multiple tasks at once"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = create_project_impl(
            api_client, project_title, task_titles, project_type
        )

        # Estimate API calls: 1 for project + 1 per task
        api_calls = 1 + len(task_titles)

        return create_simple_response(
            data=result,
            summary_text=f"Created project '{project_title}' with {len(task_titles)} tasks",
            api_endpoint="/addCategory + /addTask",
            api_calls_made=api_calls,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to create project with tasks")
        return create_error_response(e, "/addCategory + /addTask", debug, start_time)


@mcp.tool()
async def get_project_overview(
    project_id: str, debug: bool = False
) -> StandardResponse:
    """Get comprehensive overview of a project including tasks and progress"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = get_project_overview_impl(api_client, project_id)

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved overview for project {project_id}",
            api_endpoint="/categories + /children",
            api_calls_made=2,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get project overview for %s", project_id)
        return create_error_response(e, "/categories + /children", debug, start_time)


@mcp.tool()
async def get_daily_productivity_overview(debug: bool = False) -> StandardResponse:
    """Get comprehensive daily productivity overview with today's tasks, overdue items, completed items, and planning insights.

    Primary tool for daily planning and productivity. Consolidates multiple data sources efficiently.
    Use when you need a complete view of today's work situation.

    For specific data only, use: get_tasks() (today's scheduled), get_due_items() (overdue),
    get_all_tasks() (comprehensive search), or get_completed_tasks() (recent completions).
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = get_daily_productivity_overview_impl(api_client)

        return create_simple_response(
            data=result,
            summary_text="Retrieved comprehensive daily productivity overview",
            api_endpoint="/todayItems + /dueItems + /doneItems",
            api_calls_made=3,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get daily productivity overview")
        return create_error_response(
            e, "/todayItems + /dueItems + /doneItems", debug, start_time
        )


@mcp.tool()
async def batch_create_tasks(
    task_list: list[str],
    project_id: str | None = None,
    category_id: str | None = None,
    debug: bool = False,
) -> StandardResponse:
    """Create multiple tasks at once with optional project/category assignment"""
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = batch_create_tasks_impl(api_client, task_list, project_id, category_id)

        return create_simple_response(
            data=result,
            summary_text=f"Created {result.get('success_count', 0)} tasks in batch",
            api_endpoint="/addTask",
            api_calls_made=len(task_list),
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to batch create tasks")
        return create_error_response(e, "/addTask", debug, start_time)


@mcp.tool()
async def batch_mark_done(task_ids: list[str], debug: bool = False) -> StandardResponse:
    """Mark multiple tasks as done at once"""
    start_time = time.time()
    try:
        api_client = create_api_client()

        completed_tasks = []
        failed_tasks = []

        for task_id in task_ids:
            try:
                completed_task = api_client.mark_task_done(task_id)
                completed_tasks.append(completed_task)
            except Exception as e:
                failed_tasks.append({"task_id": task_id, "error": str(e)})

        result = {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_count": len(completed_tasks),
            "failure_count": len(failed_tasks),
            "total_requested": len(task_ids),
        }

        return create_simple_response(
            data=result,
            summary_text=f"Marked {len(completed_tasks)} of {len(task_ids)} tasks as done",
            api_endpoint="/markDone",
            api_calls_made=len(task_ids),
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to batch mark tasks done")
        return create_error_response(e, "/markDone", debug, start_time)


@mcp.tool()
async def time_tracking_summary(debug: bool = False) -> StandardResponse:
    """Get time tracking overview and productivity insights.

    Use when you need to check current time tracking status and get productivity metrics.
    For starting/stopping tracking, use start_time_tracking() or stop_time_tracking().
    For daily productivity overview, use get_daily_productivity_overview().
    """
    start_time = time.time()
    try:
        api_client = create_api_client()

        # Get currently tracked item
        tracked_item = api_client.get_currently_tracked_item()

        # Get account info which may include time tracking stats
        account = api_client.get_account_info()

        # Get kudos info for productivity rewards
        kudos = api_client.get_kudos_info()

        is_tracking = tracked_item and "message" not in tracked_item

        result = {
            "currently_tracking": is_tracking,
            "tracked_item": tracked_item if is_tracking else None,
            "account_stats": account,
            "kudos_info": kudos,
            "tracking_status": "Active" if is_tracking else "Not tracking",
            "suggestion": "Start tracking a task to measure productivity"
            if not is_tracking
            else f"Currently tracking: {tracked_item.get('title', 'Unknown task')}",
        }

        return create_simple_response(
            data=result,
            summary_text="Active time tracking"
            if is_tracking
            else "No active time tracking",
            api_endpoint="/me/currentlyTrackedItem + /me + /me/kudos",
            api_calls_made=3,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get time tracking summary")
        return create_error_response(
            e, "/me/currentlyTrackedItem + /me + /me/kudos", debug, start_time
        )


@mcp.tool()
async def get_completed_tasks(debug: bool = False) -> StandardResponse:
    """Get completed tasks from past 7 days with efficient date filtering and categorization.

    Use when you need to review recent accomplishments or productivity patterns.
    For specific date, use get_completed_tasks_for_date(date).
    For custom time ranges, use get_productivity_summary_for_time_range().
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = get_completed_tasks_impl(api_client)

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved {result.get('total_completed', 0)} completed tasks from past 7 days",
            api_endpoint="/doneItems",
            api_calls_made=7,  # One call per day for 7 days
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get completed tasks")
        return create_error_response(e, "/doneItems", debug, start_time)


@mcp.tool()
async def get_productivity_summary_for_time_range(
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    debug: bool = False,
) -> StandardResponse:
    """Get a comprehensive productivity summary for a specified time range

    Args:
        days: Number of days to analyze from today backwards (default: 7 for weekly summary)
              Examples: 1 (today only), 7 (past week), 30 (past month)
        start_date: Start date in YYYY-MM-DD format (overrides days parameter)
        end_date: End date in YYYY-MM-DD format (defaults to today if start_date provided)

    Examples:
        - get_productivity_summary_for_time_range(days=30)  # Past 30 days
        - get_productivity_summary_for_time_range(start_date='2025-06-01', end_date='2025-06-10')
        - get_productivity_summary_for_time_range(start_date='2025-06-01')  # June 1st to today
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        result = get_productivity_summary_for_time_range_impl(
            api_client, days, start_date, end_date
        )

        # Estimate API calls based on date range
        estimated_days = days or 7
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            estimated_days = (end - start).days + 1

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved productivity summary for {estimated_days} days",
            api_endpoint="/doneItems",
            api_calls_made=estimated_days,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get productivity summary")
        return create_error_response(e, "/doneItems", debug, start_time)


@mcp.tool()
async def get_completed_tasks_for_date(
    date: str, debug: bool = False
) -> StandardResponse:
    """Get completed tasks for a specific date using efficient API filtering

    Args:
        date: Date in YYYY-MM-DD format (e.g., '2025-06-13')
    """
    start_time = time.time()
    try:
        api_client = create_api_client()
        completed_items = api_client.get_done_items(date=date)

        # Group by project for better organization
        by_project: dict[str, list[dict[str, Any]]] = {}
        unassigned: list[dict[str, Any]] = []

        for item in completed_items:
            parent_id = item.get("parentId", "unassigned")

            if parent_id == "unassigned":
                unassigned.append(item)
            else:
                if parent_id not in by_project:
                    by_project[parent_id] = []
                by_project[parent_id].append(item)

        result = {
            "date": date,
            "total_completed": len(completed_items),
            "completed_by_project": by_project,
            "unassigned_completed": unassigned,
            "project_count": len(by_project),
            "unassigned_count": len(unassigned),
            "all_completed": completed_items,
            "source": f"Efficiently filtered from /doneItems?date={date}",
        }

        return create_simple_response(
            data=result,
            summary_text=f"Retrieved {len(completed_items)} completed tasks for {date}",
            api_endpoint="/doneItems",
            api_calls_made=1,
            debug=debug,
            start_time=start_time,
        )
    except Exception as e:
        logger.exception("Failed to get completed tasks for %s", date)
        return create_error_response(e, "/doneItems", debug, start_time)


def start():
    """Start the MCP server"""
    mcp.run()


if __name__ == "__main__":
    start()
    """Start the MCP server"""
    mcp.run()


if __name__ == "__main__":
    start()
