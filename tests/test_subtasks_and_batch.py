"""Offline tests for update_subtasks, batch creation pacing and the rate limiter.

HTTP is mocked at the ``requests`` layer, so no Marvin account is needed.
"""

import copy
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from amazing_marvin_mcp.api import MarvinAPIClient
from amazing_marvin_mcp.rate_limit import DailyLimitExceededError, RateLimiter
from amazing_marvin_mcp.subtasks import update_subtasks
from amazing_marvin_mcp.tasks import batch_create_tasks

TASK_ID = "task123"


class FakeTime:
    """Clock whose sleep advances time instantly and records each wait."""

    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []
        self.day = date(2026, 1, 1)

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def today(self) -> date:
        return self.day

    def limiter(self, daily_limit: int = 1440) -> RateLimiter:
        return RateLimiter(
            daily_limit=daily_limit,
            clock=self.clock,
            sleep=self.sleep,
            today=self.today,
        )


def _response(payload: Any, status: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.content = b"x"
    response.json.return_value = copy.deepcopy(payload)
    if status >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status} error", response=response
        )
    return response


class FakeMarvin:
    """Minimal in-memory stand-in for /doc, /doc/update and /addTask."""

    def __init__(self, subtasks: dict | None = None, db: str = "Tasks"):
        self.doc: dict[str, Any] = {"_id": TASK_ID, "db": db, "title": "Groceries"}
        if subtasks is not None:
            self.doc["subtasks"] = subtasks
        self.posts: list[tuple[str, dict, dict]] = []
        self.gets: list[tuple[str, dict]] = []
        self.add_task_statuses: list[int] = []
        self.stored_subtasks_override: dict | None = None

    def get(self, url, headers):
        self.gets.append((url, headers))
        if self.stored_subtasks_override is not None and len(self.gets) > 1:
            return _response({**self.doc, "subtasks": self.stored_subtasks_override})
        return _response(self.doc)

    def post(self, url, headers, json):
        self.posts.append((url, headers, json))
        if url.endswith("/doc/update"):
            for setter in json["setters"]:
                self.doc[setter["key"]] = setter["val"]
            return _response(self.doc)
        status = self.add_task_statuses.pop(0) if self.add_task_statuses else 200
        return _response({"_id": f"new{len(self.posts)}", **json}, status)


@pytest.fixture
def fake_time():
    return FakeTime()


def _run_update(marvin: FakeMarvin, fake_time: FakeTime, **changes):
    client = MarvinAPIClient(api_key="api", full_access_token="full")
    with (
        patch("amazing_marvin_mcp.api.requests.get", side_effect=marvin.get),
        patch("amazing_marvin_mcp.api.requests.post", side_effect=marvin.post),
    ):
        return update_subtasks(
            client, TASK_ID, rate_limiter=fake_time.limiter(), **changes
        )


def _existing() -> dict:
    return {
        "a1": {"_id": "a1", "title": "Milk", "done": False, "rank": 1},
        "b2": {"_id": "b2", "title": "Eggs", "done": True, "rank": 2},
    }


class TestUpdateSubtasks:
    def test_add_sends_validated_setters_with_full_access_token(self, fake_time):
        marvin = FakeMarvin(_existing())

        result = _run_update(
            marvin, fake_time, add=["Bread", {"title": "Jam", "timeEstimate": 60000}]
        )

        assert len(marvin.posts) == 1
        url, headers, body = marvin.posts[0]
        assert url.endswith("/doc/update")
        assert headers == {"X-Full-Access-Token": "full"}
        assert body["itemId"] == TASK_ID
        keys = [s["key"] for s in body["setters"]]
        assert keys == ["subtasks", "fieldUpdates.subtasks", "updatedAt"]
        sent = body["setters"][0]["val"]
        assert sent["a1"] == _existing()["a1"]
        added = sorted(
            (s for k, s in sent.items() if k not in _existing()),
            key=lambda s: s["rank"],
        )
        assert [(s["title"], s["done"], s["rank"]) for s in added] == [
            ("Bread", False, 3),
            ("Jam", False, 4),
        ]
        assert added[1]["timeEstimate"] == 60000
        assert all(s["_id"] == k for k, s in sent.items())
        assert body["setters"][1]["val"] == body["setters"][2]["val"]
        assert result["subtask_count"] == 4
        assert result["matches_request"] is True

    def test_tick_and_untick_by_title_or_id(self, fake_time):
        marvin = FakeMarvin(_existing())

        result = _run_update(marvin, fake_time, tick=["Milk"], untick=["b2"])

        assert result["subtasks"]["a1"]["done"] is True
        assert result["subtasks"]["b2"]["done"] is False
        assert result["done_count"] == 1

    def test_set_replaces_all_subtasks(self, fake_time):
        marvin = FakeMarvin(_existing())

        result = _run_update(marvin, fake_time, set_subtasks=["Only one"])

        assert [s["title"] for s in result["subtasks"].values()] == ["Only one"]

    def test_returns_what_marvin_stored_after_reconcile_read(self, fake_time):
        marvin = FakeMarvin(_existing())
        stored_by_server = {"z9": {"_id": "z9", "title": "X", "done": False, "rank": 1}}
        marvin.stored_subtasks_override = stored_by_server

        result = _run_update(marvin, fake_time, add=["Bread"])

        assert result["subtasks"] == stored_by_server
        assert result["matches_request"] is False
        assert len(marvin.gets) == 2

    @pytest.mark.parametrize(
        "changes",
        [
            {"add": [{"title": "Bad", "timeEstimate": -5}]},
            {"add": [{"title": "Bad", "timeEstimate": "1h"}]},
            {"add": [{"title": "Bad", "rank": 1}]},
            {"add": [""]},
            {"add": [{"title": "Bad", "done": "yes"}]},
            {"tick": ["Nope"]},
            {"tick": ["Milk"], "untick": ["a1"]},
            {},
        ],
    )
    def test_invalid_changes_never_reach_doc_update(self, fake_time, changes):
        marvin = FakeMarvin(_existing())

        with pytest.raises((ValueError, TypeError)):
            _run_update(marvin, fake_time, **changes)

        assert marvin.posts == []

    def test_ambiguous_title_is_rejected(self, fake_time):
        dupes = {
            "a1": {"_id": "a1", "title": "Milk", "done": False, "rank": 1},
            "b2": {"_id": "b2", "title": "Milk", "done": False, "rank": 2},
        }
        marvin = FakeMarvin(dupes)

        with pytest.raises(ValueError, match="ambiguous"):
            _run_update(marvin, fake_time, tick=["Milk"])
        assert marvin.posts == []

    def test_malformed_existing_subtask_blocks_update(self, fake_time):
        marvin = FakeMarvin({"a1": {"_id": "other", "title": "Milk", "done": False}})

        with pytest.raises(ValueError, match="mismatched _id"):
            _run_update(marvin, fake_time, add=["Bread"])
        assert marvin.posts == []

    def test_refuses_non_task_documents(self, fake_time):
        marvin = FakeMarvin(db="ProfileItems")

        with pytest.raises(ValueError, match="not a task"):
            _run_update(marvin, fake_time, add=["Bread"])
        assert marvin.posts == []

    def test_requires_full_access_token(self, fake_time):
        client = MarvinAPIClient(api_key="api")
        with (
            patch("amazing_marvin_mcp.api.requests.get") as get,
            patch("amazing_marvin_mcp.api.requests.post") as post,
            pytest.raises(ValueError, match="FULL_ACCESS_TOKEN"),
        ):
            update_subtasks(
                client, TASK_ID, add=["Bread"], rate_limiter=fake_time.limiter()
            )
        get.assert_not_called()
        post.assert_not_called()

    def test_paces_requests(self, fake_time):
        marvin = FakeMarvin(_existing())

        _run_update(marvin, fake_time, add=["Bread"])

        # read -> write waits 1s, write -> reconcile read waits 3s
        assert fake_time.sleeps == [1.0, 3.0]


class TestRateLimiter:
    def test_spaces_requests_by_min_interval(self, fake_time):
        limiter = fake_time.limiter()

        limiter.acquire(1.0)
        fake_time.now += 0.25
        limiter.acquire(1.0)
        limiter.acquire(1.0)

        assert fake_time.sleeps == [0.75, 1.0]

    def test_daily_budget_and_reset_on_new_day(self, fake_time):
        limiter = fake_time.limiter(daily_limit=2)
        limiter.acquire(0)
        limiter.acquire(0)

        with pytest.raises(DailyLimitExceededError):
            limiter.acquire(0)
        assert limiter.remaining_today == 0

        fake_time.day = date(2026, 1, 2)
        assert limiter.remaining_today == 2
        limiter.acquire(0)


def _run_batch(marvin: FakeMarvin, limiter: RateLimiter, tasks: list):
    client = MarvinAPIClient(api_key="api")
    with patch("amazing_marvin_mcp.api.requests.post", side_effect=marvin.post):
        return batch_create_tasks(client, tasks, project_id="p1", rate_limiter=limiter)


class TestBatchCreateTasks:
    def test_creates_at_most_one_task_per_second(self, fake_time):
        marvin = FakeMarvin()

        result = _run_batch(marvin, fake_time.limiter(), ["A", "B", "C"])

        assert result["success_count"] == 3
        assert fake_time.sleeps == [1.0, 1.0]
        assert [body["title"] for _, _, body in marvin.posts] == ["A", "B", "C"]
        assert all(body["parentId"] == "p1" for _, _, body in marvin.posts)
        assert all(headers == {"X-API-Token": "api"} for _, headers, _ in marvin.posts)

    def test_stops_with_partial_results_when_daily_budget_runs_out(self, fake_time):
        marvin = FakeMarvin()

        result = _run_batch(marvin, fake_time.limiter(daily_limit=2), ["A", "B", "C"])

        assert result["success_count"] == 2
        assert result["skipped_tasks"] == ["C"]
        assert "Daily" in result["stopped_reason"]
        assert result["daily_budget_remaining"] == 0
        assert len(marvin.posts) == 2

    def test_stops_on_http_429(self, fake_time):
        marvin = FakeMarvin()
        marvin.add_task_statuses = [200, 429]

        result = _run_batch(marvin, fake_time.limiter(), ["A", "B", "C", "D"])

        assert result["success_count"] == 1
        assert result["failure_count"] == 1
        assert result["failed_tasks"][0]["task"] == "B"
        assert result["skipped_tasks"] == ["C", "D"]
        assert "429" in result["stopped_reason"]
        assert len(marvin.posts) == 2

    def test_other_failures_do_not_stop_the_batch(self, fake_time):
        marvin = FakeMarvin()
        marvin.add_task_statuses = [500, 200]

        result = _run_batch(marvin, fake_time.limiter(), ["A", "B"])

        assert result["success_count"] == 1
        assert result["failure_count"] == 1
        assert result["skipped_tasks"] == []
        assert result["stopped_reason"] is None
