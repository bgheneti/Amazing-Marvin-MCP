"""Checklist subtask editing for Amazing Marvin MCP.

Marvin stores subtasks inside the task document as
``{id: {"_id", "title", "done", "rank", "timeEstimate"?}}``. They can only be
changed through the experimental ``/doc/update`` endpoint, where a wrongly
shaped value can crash the Marvin app, so every new value is validated before
it is sent.
"""

import copy
import logging
import secrets
import string
import time
from typing import Any

from .api import MarvinAPIClient
from .rate_limit import (
    CREATE_INTERVAL_SECONDS,
    QUERY_INTERVAL_SECONDS,
    RateLimiter,
    default_rate_limiter,
)

logger = logging.getLogger(__name__)

SUBTASK_ID_LENGTH = 13
_ID_ALPHABET = string.ascii_letters + string.digits
_INPUT_KEYS = {"title", "done", "timeEstimate"}


def _new_subtask_id(taken: set[str]) -> str:
    while True:
        subtask_id = "".join(
            secrets.choice(_ID_ALPHABET) for _ in range(SUBTASK_ID_LENGTH)
        )
        if subtask_id not in taken:
            return subtask_id


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _parse_input(item: str | dict[str, Any]) -> dict[str, Any]:
    """Turn a title or {title, done?, timeEstimate?} into subtask fields."""
    fields = {"title": item} if isinstance(item, str) else item
    if not isinstance(fields, dict):
        raise TypeError(f"Subtask must be a title or an object, got {item!r}")
    unknown = set(fields) - _INPUT_KEYS
    if unknown:
        raise ValueError(f"Unsupported subtask fields: {sorted(unknown)}")
    title = fields.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"Subtask title must be a non-empty string: {item!r}")
    parsed: dict[str, Any] = {
        "title": title.strip(),
        "done": fields.get("done", False),
    }
    if "timeEstimate" in fields:
        parsed["timeEstimate"] = fields["timeEstimate"]
    return parsed


def _resolve(subtasks: dict[str, dict[str, Any]], ref: str) -> str:
    """Find a subtask ID from an ID or an exact title."""
    if ref in subtasks:
        return ref
    matches = [sid for sid, sub in subtasks.items() if sub.get("title") == ref]
    if not matches:
        raise ValueError(f"No subtask with ID or title {ref!r}")
    if len(matches) > 1:
        raise ValueError(f"Subtask title {ref!r} is ambiguous; use its ID instead")
    return matches[0]


def validate_subtasks(subtasks: Any) -> None:
    """Raise ValueError unless ``subtasks`` matches Marvin's Subtask shape."""
    if not isinstance(subtasks, dict):
        raise TypeError("subtasks must be an object keyed by subtask ID")
    for key, sub in subtasks.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"Invalid subtask ID: {key!r}")
        if not isinstance(sub, dict):
            raise TypeError(f"Subtask {key} must be an object")
        if sub.get("_id") != key:
            raise ValueError(f"Subtask {key} has mismatched _id {sub.get('_id')!r}")
        if not isinstance(sub.get("title"), str):
            raise TypeError(f"Subtask {key} title must be a string")
        if not isinstance(sub.get("done"), bool):
            raise TypeError(f"Subtask {key} done must be true or false")
        if not _is_number(sub.get("rank")):
            raise TypeError(f"Subtask {key} rank must be a number")
        if "timeEstimate" in sub and (
            not _is_number(sub["timeEstimate"]) or sub["timeEstimate"] < 0
        ):
            raise ValueError(
                f"Subtask {key} timeEstimate must be a non-negative number of ms"
            )


def apply_subtask_changes(
    existing: dict[str, dict[str, Any]],
    set_subtasks: list[str | dict[str, Any]] | None = None,
    add: list[str | dict[str, Any]] | None = None,
    tick: list[str] | None = None,
    untick: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return the new subtasks dict without modifying ``existing``.

    ``set_subtasks`` replaces all subtasks; ``add`` appends; ``tick`` and
    ``untick`` take subtask IDs or exact titles.
    """
    result: dict[str, dict[str, Any]] = (
        {} if set_subtasks is not None else copy.deepcopy(existing)
    )
    ranks = [sub["rank"] for sub in result.values() if _is_number(sub.get("rank"))]
    next_rank = max(ranks, default=0) + 1

    for item in [*(set_subtasks or []), *(add or [])]:
        subtask_id = _new_subtask_id(set(result) | set(existing))
        result[subtask_id] = {
            "_id": subtask_id,
            **_parse_input(item),
            "rank": next_rank,
        }
        next_rank += 1

    tick_ids = {_resolve(result, ref) for ref in tick or []}
    untick_ids = {_resolve(result, ref) for ref in untick or []}
    both = tick_ids & untick_ids
    if both:
        raise ValueError(f"Subtasks both ticked and unticked: {sorted(both)}")
    for subtask_id in tick_ids:
        result[subtask_id]["done"] = True
    for subtask_id in untick_ids:
        result[subtask_id]["done"] = False
    return result


def update_subtasks(
    api_client: MarvinAPIClient,
    task_id: str,
    *,
    set_subtasks: list[str | dict[str, Any]] | None = None,
    add: list[str | dict[str, Any]] | None = None,
    tick: list[str] | None = None,
    untick: list[str] | None = None,
    rate_limiter: RateLimiter = default_rate_limiter,
) -> dict[str, Any]:
    """Set, add, tick or untick a task's subtasks, then re-read the task."""
    if set_subtasks is None and not (add or tick or untick):
        raise ValueError("Nothing to change: pass set_subtasks, add, tick or untick")

    rate_limiter.acquire(QUERY_INTERVAL_SECONDS)
    task = api_client.get_document(task_id)
    if task.get("db") != "Tasks":
        raise ValueError(f"Document {task_id} is not a task (db={task.get('db')!r})")

    new_subtasks = apply_subtask_changes(
        task.get("subtasks") or {}, set_subtasks, add, tick, untick
    )
    validate_subtasks(new_subtasks)

    now_ms = int(time.time() * 1000)
    setters: list[dict[str, Any]] = [
        {"key": "subtasks", "val": new_subtasks},
        {"key": "fieldUpdates.subtasks", "val": now_ms},
        {"key": "updatedAt", "val": now_ms},
    ]
    rate_limiter.acquire(CREATE_INTERVAL_SECONDS)
    api_client.update_document(task_id, setters)

    # Reconcile: report what Marvin actually stored, not what we sent.
    rate_limiter.acquire(QUERY_INTERVAL_SECONDS)
    stored = api_client.get_document(task_id).get("subtasks") or {}

    return {
        "task_id": task_id,
        "subtasks": stored,
        "subtask_count": len(stored),
        "done_count": sum(1 for sub in stored.values() if sub.get("done")),
        "matches_request": stored == new_subtasks,
    }
