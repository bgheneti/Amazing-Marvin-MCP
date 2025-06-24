"""Task processing and cleaning functions for Amazing Marvin MCP."""

import logging
from typing import Any

from .api import MarvinAPIClient
from .response_models import CleanTask, Reference

logger = logging.getLogger(__name__)

# Field mapping for future-proofing
TASK_FIELD_MAPPING = {
    "_id": "id",
    "title": "title",
    "dueDate": "due_date",
    "note": "note",
    "done": "completed",
    "createdAt": "created_at",
    "priority": "priority",
    "scheduledTime": "scheduled_time",
    "scheduledDate": "scheduled_date",
    "isFrogged": "is_frogged",
    "timeEstimate": "time_estimate",
    "timeBlockSection": "time_block_section",
}

REFERENCE_MAPPINGS: dict[str, dict[str, Any]] = {
    "project": {"id_fields": ["parentId", "parent_id"], "lookup_source": "projects"},
    "category": {
        "id_fields": ["categoryId", "category_id"],
        "lookup_source": "categories",
    },
    "labels": {
        "id_fields": ["labelIds", "labels"],
        "lookup_source": "labels",
        "is_array": True,
    },
}


def create_lookup_maps(api_client: MarvinAPIClient) -> dict[str, dict[str, str]]:
    """Create lookup maps for resolving references."""
    try:
        projects = api_client.get_projects()
        categories = api_client.get_categories()
        labels = api_client.get_labels()

        lookup_maps = {
            "projects": {
                str(p["_id"]): str(p["title"])
                for p in projects
                if p.get("_id") and p.get("title")
            },
            "categories": {
                str(c["_id"]): str(c["title"])
                for c in categories
                if c.get("_id") and c.get("title")
            },
            "labels": {
                str(label["_id"]): str(label["title"])
                for label in labels
                if label.get("_id") and label.get("title")
            },
        }

        logger.debug(
            "Created lookup maps: %d projects, %d categories, %d labels",
            len(lookup_maps["projects"]),
            len(lookup_maps["categories"]),
            len(lookup_maps["labels"]),
        )

    except Exception:
        logger.exception("Failed to create lookup maps")
        return {"projects": {}, "categories": {}, "labels": {}}
    else:
        return lookup_maps


def _extract_basic_fields(raw_task: dict[str, Any]) -> dict[str, Any]:
    """Extract and map basic fields from raw task data."""
    clean_data = {}
    for api_field, clean_field in TASK_FIELD_MAPPING.items():
        if api_field in raw_task and raw_task[api_field] is not None:
            clean_data[clean_field] = raw_task[api_field]
    return clean_data


def _process_references(
    raw_task: dict[str, Any], lookup_maps: dict[str, dict[str, str]]
) -> tuple[dict[str, Any], set[str]]:
    """Process reference fields and return references dict and mapped fields set."""
    references: dict[str, Any] = {}
    all_mapped_fields = set(TASK_FIELD_MAPPING.keys())

    for ref_name, ref_config in REFERENCE_MAPPINGS.items():
        possible_id_fields = ref_config["id_fields"]
        lookup_source = ref_config["lookup_source"]
        is_array = ref_config.get("is_array", False)

        ref_id = None
        # Try each possible field name for this reference
        for field_name in possible_id_fields:
            if raw_task.get(field_name):
                ref_id = raw_task[field_name]
                all_mapped_fields.add(field_name)
                break

        if not ref_id:
            continue

        if is_array and isinstance(ref_id, list):
            refs = []
            for rid in ref_id:
                name = lookup_maps[lookup_source].get(str(rid))
                if name:
                    refs.append(Reference(item_id=str(rid), name=name))
            references[ref_name] = refs if refs else None
        else:
            name = lookup_maps[lookup_source].get(str(ref_id))
            if name:
                references[ref_name] = Reference(item_id=str(ref_id), name=name)

    return references, all_mapped_fields


def _collect_unmapped_fields(
    raw_task: dict[str, Any], all_mapped_fields: set[str]
) -> dict[str, Any]:
    """Collect and process unmapped fields from raw task data."""
    skip_fields = {"db", "_rev"}
    all_mapped_fields.update(skip_fields)
    other_fields = {}

    for key, value in raw_task.items():
        if key not in all_mapped_fields and value is not None:
            snake_case_key = "".join(
                ["_" + c.lower() if c.isupper() else c for c in key]
            ).lstrip("_")
            other_fields[snake_case_key] = value
            if "frog" in key.lower() or (
                isinstance(value, str) and "frog" in value.lower()
            ):
                logger.info("Frog-related field detected: %s = %s", key, value)

    return other_fields


def _check_api_changes(
    raw_task: dict[str, Any], other_fields: dict[str, Any]
) -> list[str]:
    """Check for potential API changes and generate warnings."""
    warnings = []
    skip_fields = {"db", "_rev"}
    unmapped_count = len(other_fields)
    total_fields = len(raw_task) - len(skip_fields & set(raw_task.keys()))
    unmapped_ratio = unmapped_count / total_fields if total_fields > 0 else 0

    title = raw_task.get("title", "Unknown")
    if unmapped_ratio > 0.3:
        field_preview = list(other_fields.keys())[:5]
        suffix = "..." if unmapped_count > 5 else ""
        warning_msg = f"High unmapped field ratio ({unmapped_ratio:.1%}) in task '{title}' - possible API changes. Unmapped fields: {field_preview}{suffix}"
        warnings.append(warning_msg)
        logger.warning("API change warning: %s", warning_msg)
    elif unmapped_count > 7:
        warning_msg = f"Many unmapped fields ({unmapped_count}) in task '{title}' - consider updating field mapping"
        warnings.append(warning_msg)
        logger.info("Field mapping suggestion: %s", warning_msg)

    return warnings


def create_clean_task(
    raw_task: dict[str, Any], lookup_maps: dict[str, dict[str, str]]
) -> tuple[CleanTask, list[str]]:
    """Convert raw API task to clean task with reference resolution and API change detection."""
    clean_data = _extract_basic_fields(raw_task)
    references, all_mapped_fields = _process_references(raw_task, lookup_maps)
    other_fields = _collect_unmapped_fields(raw_task, all_mapped_fields)
    warnings = _check_api_changes(raw_task, other_fields)

    clean_task = CleanTask(
        task_id=str(clean_data.get("id", "")),
        title=clean_data.get("title", "Untitled"),
        due_date=clean_data.get("due_date"),
        priority=clean_data.get("priority"),
        scheduled_time=clean_data.get("scheduled_time"),
        completed=clean_data.get("completed", False),
        created_at=clean_data.get("created_at"),
        note=clean_data.get("note"),
        is_frogged=bool(clean_data.get("is_frogged", False)),
        time_estimate=clean_data.get("time_estimate"),
        time_block_section=clean_data.get("time_block_section"),
        project=references.get("project"),
        category=references.get("category"),
        labels=references.get("labels"),
        other=other_fields if other_fields else None,
    )

    return clean_task, warnings


def process_tasks(
    api_client: MarvinAPIClient, raw_tasks: list[dict]
) -> tuple[list[CleanTask], list[str]]:
    """Process multiple raw tasks into clean tasks with warnings."""
    lookup_maps = create_lookup_maps(api_client)

    clean_tasks = []
    all_warnings = []

    for raw_task in raw_tasks:
        try:
            clean_task, task_warnings = create_clean_task(raw_task, lookup_maps)
            clean_tasks.append(clean_task)
            all_warnings.extend(task_warnings)
        except Exception:
            logger.exception(
                "Failed to process task %s", raw_task.get("_id", "unknown")
            )
            # Continue processing other tasks

    logger.debug(
        "Processed %d tasks with %d warnings", len(clean_tasks), len(all_warnings)
    )

    return clean_tasks, all_warnings
