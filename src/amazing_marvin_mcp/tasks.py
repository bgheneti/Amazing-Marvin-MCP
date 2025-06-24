"""Task management functions for Amazing Marvin MCP."""

import itertools
import logging
from datetime import datetime
from typing import Any

from .api import MarvinAPIClient

logger = logging.getLogger(__name__)


def get_daily_focus(api_client: MarvinAPIClient) -> dict[str, Any]:
    """Get today's focus items - due items, scheduled tasks, and completed tasks."""
    # Get today's items and due items
    today_items = api_client.get_tasks()  # This gets todayItems
    due_items = api_client.get_due_items()

    # Get today's completed tasks (API defaults to today if no date provided)
    today_completed = api_client.get_done_items()

    # Combine scheduled/due items (these are pending by nature from todayItems)
    all_pending_items = []
    item_ids = set()

    for item in today_items + due_items:
        item_id = item.get("_id")
        if item_id and item_id not in item_ids:
            all_pending_items.append(item)
            item_ids.add(item_id)

    # Categorize pending items by priority or type
    high_priority = [
        item for item in all_pending_items if item.get("priority") == "high"
    ]
    projects = [item for item in all_pending_items if item.get("type") == "project"]
    tasks = [item for item in all_pending_items if item.get("type") != "project"]

    return {
        "total_focus_items": len(all_pending_items) + len(today_completed),
        "completed_today": len(today_completed),
        "pending_items": len(all_pending_items),
        "high_priority_items": high_priority,
        "projects": projects,
        "tasks": tasks,
        "completed_items": today_completed,
        "pending_scheduled_items": all_pending_items,
        "productivity_note": f"You've completed {len(today_completed)} items today!"
        if today_completed
        else "No completed items yet today - keep going!",
    }


def batch_create_tasks(
    api_client: MarvinAPIClient,
    task_list: list[Any],
    project_id: str | None = None,
    category_id: str | None = None,
) -> dict[str, Any]:
    """Create multiple tasks at once with optional project/category assignment."""
    created_tasks = []
    failed_tasks = []

    for task_info in task_list:
        try:
            # Handle both string titles and dict objects
            if isinstance(task_info, str):
                task_data = {"title": task_info}
            else:
                task_data = task_info.copy()

            # Add project/category if specified
            if project_id and "parentId" not in task_data:
                task_data["parentId"] = project_id
            if category_id and "categoryId" not in task_data:
                task_data["categoryId"] = category_id

            created_task = api_client.create_task(task_data)
            created_tasks.append(created_task)
        except Exception as e:
            failed_tasks.append({"task": task_info, "error": str(e)})

    return {
        "created_tasks": created_tasks,
        "failed_tasks": failed_tasks,
        "success_count": len(created_tasks),
        "failure_count": len(failed_tasks),
        "total_requested": len(task_list),
    }


def quick_daily_planning(api_client: MarvinAPIClient) -> dict[str, Any]:
    """Get a quick daily planning overview with actionable insights."""
    # Get today's focus items
    today_items = api_client.get_tasks()
    due_items = api_client.get_due_items()

    # Get projects for context
    projects = api_client.get_projects()

    # Analyze workload
    total_due = len(due_items)
    total_scheduled = len(today_items)

    today = datetime.now().strftime("%Y-%m-%d")

    # Simple prioritization suggestions
    heavy_day_threshold = 5
    suggestions = []
    if total_due > 0:
        suggestions.append(f"Focus on {total_due} overdue items first")
    if total_scheduled > heavy_day_threshold:
        suggestions.append("Consider rescheduling some tasks - you have a heavy day")
    if total_scheduled == 0 and total_due == 0:
        suggestions.append("Great! No urgent tasks today - time to work on your goals")

    return {
        "planning_date": today,
        "overdue_items": total_due,
        "scheduled_today": total_scheduled,
        "active_projects": len(projects),
        "suggestions": suggestions,
        "due_items": due_items[:5],  # Show first 5 due items
        "today_items": today_items[:5],  # Show first 5 scheduled items
        "quick_summary": f"{total_due} due, {total_scheduled} scheduled",
    }


def _get_all_children_recursive(
    api_client: MarvinAPIClient, parent_id: str, visited: set[str] | None = None
) -> list[dict[str, Any]]:
    """Recursively get all children of a parent item, avoiding infinite loops."""
    if visited is None:
        visited = set()

    if parent_id in visited:
        logger.warning("Circular reference detected for parent_id %s", parent_id)
        return []

    visited.add(parent_id)

    try:
        direct_children = api_client.get_children(parent_id)
        all_children = list(direct_children)  # Copy the list

        # Recursively get children of each child
        for child in direct_children:
            child_id = child.get("_id")
            if child_id:
                grandchildren = _get_all_children_recursive(
                    api_client, child_id, visited.copy()
                )
                all_children.extend(grandchildren)

    except Exception as e:
        logger.warning("Failed to get children for parent_id %s: %s", parent_id, e)
        return []
    else:
        return all_children


def get_child_tasks_recursive(
    api_client: MarvinAPIClient, parent_id: str
) -> dict[str, Any]:
    """Get child tasks recursively with comprehensive information."""
    all_children = _get_all_children_recursive(api_client, parent_id)

    # Categorize children by type
    tasks = [item for item in all_children if item.get("type") != "project"]
    projects = [item for item in all_children if item.get("type") == "project"]

    return {
        "parent_id": parent_id,
        "total_children": len(all_children),
        "tasks": tasks,
        "projects": projects,
        "task_count": len(tasks),
        "project_count": len(projects),
        "all_children": all_children,
        "recursive": True,
    }


def get_all_nested_items(
    items: list[dict[str, Any]], api_client: MarvinAPIClient
) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []
    item_ids = set()

    for item in items:
        item_id = item.get("_id")
        if item_id and item_id not in item_ids:
            all_items.append(item)
            item_ids.add(item_id)

    # For each project/category, recursively get all children
    for item in list(all_items):  # Create a copy to avoid modifying while iterating
        item_id = item.get("_id")
        item_type = item.get("type")
        if not item_id or (item_type not in ["project", "category"]):
            continue
        children = _get_all_children_recursive(api_client, item_id)
        for child in children:
            child_id = child.get("_id")
            if child_id and child_id not in item_ids:
                all_items.append(child)
                item_ids.add(child_id)
    return all_items


def get_all_tasks_impl(
    api_client: MarvinAPIClient, label: str | None = None
) -> dict[str, Any]:
    """Get all tasks and projects with optional label filtering, using recursive traversal."""
    try:
        # Get all top-level items
        today_items = api_client.get_tasks()
        due_items = api_client.get_due_items()
        projects = api_client.get_projects()
        categories = api_client.get_categories()

        all_items = get_all_nested_items(
            list(itertools.chain(*[today_items, due_items, projects, categories])),
            api_client=api_client,
        )

        # Filter by label if specified
        if label:
            # Get all labels to understand the label structure
            labels = api_client.get_labels()

            # Find the label ID
            label_id = None
            for lbl in labels:
                if lbl.get("title", "").lower() == label.lower():
                    label_id = lbl.get("_id")
                    break

            if label_id:
                filtered_items = []
                for item in all_items:
                    item_labels = item.get("labelIds", [])
                    if label_id in item_labels:
                        filtered_items.append(item)
                all_items = filtered_items
            else:
                # If label not found, return empty results
                all_items = []

        # Filter to only tasks (not projects or categories)
        tasks = [
            item
            for item in all_items
            if item.get("type") not in ["project", "category"]
        ]

        return {
            "tasks": tasks,
            "task_count": len(tasks),
            "filter_applied": label is not None,
            "label_filter": label,
            "source": "Recursive traversal of all items",
        }

    except Exception as e:
        logger.exception("Failed to get all tasks")
        return {"error": str(e), "tasks": [], "task_count": 0}
