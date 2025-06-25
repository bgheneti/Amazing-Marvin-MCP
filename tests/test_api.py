"""Pytest tests for Amazing Marvin MCP API functionality."""

from datetime import datetime

import pytest
import requests
from amazing_marvin_mcp.analytics import get_productivity_summary
from amazing_marvin_mcp.api import MarvinAPIClient, create_api_client
from amazing_marvin_mcp.config import get_settings
from amazing_marvin_mcp.projects import create_project_with_tasks
from amazing_marvin_mcp.tasks import (
    batch_create_tasks,
    get_daily_focus,
    quick_daily_planning,
)

# Constants for tests
TASK_COUNT = 3  # Number of tasks to create in tests


@pytest.fixture()
def api_client():
    """Create API client for testing."""
    try:
        settings = get_settings()
        if not settings.amazing_marvin_api_key:
            pytest.skip("No API key available for testing")
        return MarvinAPIClient(api_key=settings.amazing_marvin_api_key)
    except Exception:
        pytest.skip("Configuration error - cannot create API client")


@pytest.fixture()
def test_project_data():
    """Test project data."""
    return {
        "title": f"Pytest Test Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "type": "project",
    }


@pytest.fixture()
def test_task_data():
    """Test task data."""
    return {
        "title": f"Pytest Test Task - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "note": "This is a test task created by pytest",
    }


class TestMarvinAPIClient:
    """Test the MarvinAPIClient class."""

    def test_api_connection(self, api_client):
        """Test API connection."""
        result = api_client.test_api_connection()
        assert result == "OK"

    def test_get_categories(self, api_client):
        """Test getting categories."""
        categories = api_client.get_categories()
        assert isinstance(categories, list)

    def test_get_projects(self, api_client):
        """Test getting projects."""
        projects = api_client.get_projects()
        assert isinstance(projects, list)

    def test_get_labels(self, api_client):
        """Test getting labels."""
        labels = api_client.get_labels()
        assert isinstance(labels, list)

    def test_get_due_items(self, api_client):
        """Test getting due items."""
        due_items = api_client.get_due_items()
        assert isinstance(due_items, list)

    def test_get_goals(self, api_client):
        """Test getting goals."""
        goals = api_client.get_goals()
        assert isinstance(goals, list)

    def test_get_account_info(self, api_client):
        """Test getting account info."""
        account = api_client.get_account_info()
        assert isinstance(account, dict)

    def test_get_currently_tracked_item(self, api_client):
        """Test getting currently tracked item."""
        tracked = api_client.get_currently_tracked_item()
        assert tracked is not None


class TestTaskAndProjectManagement:
    """Test task and project creation, modification, and deletion."""

    def test_create_project(self, api_client, test_project_data):
        """Test creating a project."""
        created_project = api_client.create_project(test_project_data)
        assert created_project is not None
        assert created_project.get("title") == test_project_data["title"]
        assert "_id" in created_project

    def test_create_task(self, api_client, test_task_data):
        """Test creating a task."""
        created_task = api_client.create_task(test_task_data)
        assert created_task is not None
        assert created_task.get("title") == test_task_data["title"]
        assert "_id" in created_task

    def test_comprehensive_workflow(
        self, api_client, test_project_data, test_task_data
    ):
        """Test a complete workflow: create project, add tasks, manage tasks."""
        # Create test project
        created_project = api_client.create_project(test_project_data)
        project_id = created_project.get("_id")
        assert project_id is not None

        # Create tasks in the project
        test_tasks = []
        for i in range(3):
            task_data = {
                **test_task_data,
                "title": f"{test_task_data['title']} #{i+1}",
                "parentId": project_id,
            }
            created_task = api_client.create_task(task_data)
            test_tasks.append(created_task)
            assert created_task.get("_id") is not None

        # Test getting children of the project
        children = api_client.get_children(project_id)
        assert isinstance(children, list)
        # Note: children might be empty if the endpoint is experimental

        # Mark first task as done
        if test_tasks and test_tasks[0].get("_id"):
            task_id = test_tasks[0]["_id"]
            completed = api_client.mark_task_done(task_id)
            assert completed is not None


class TestTimeTracking:
    """Test time tracking functionality."""

    def test_start_stop_tracking(self, api_client, test_task_data):
        """Test starting and stopping time tracking."""
        # First create a task to track
        created_task = api_client.create_task(test_task_data)
        task_id = created_task.get("_id")
        assert task_id is not None

        # Test starting tracking
        start_result = api_client.start_time_tracking(task_id)
        assert start_result is not None

        # Test stopping tracking
        stop_result = api_client.stop_time_tracking(task_id)
        assert stop_result is not None

    def test_get_time_tracks(self, api_client, test_task_data):
        """Test getting time tracking data."""
        # Create a task first
        created_task = api_client.create_task(test_task_data)
        task_id = created_task.get("_id")
        assert task_id is not None

        # Get time tracks for the task
        tracks = api_client.get_time_tracks([task_id])
        assert tracks is not None


class TestRewards:
    """Test reward system functionality."""

    def test_claim_reward_points(self, api_client, test_task_data):
        """Test claiming reward points."""
        # Create and complete a task first
        created_task = api_client.create_task(test_task_data)
        task_id = created_task.get("_id")
        assert task_id is not None

        # Mark task as done
        completed_task = api_client.mark_task_done(task_id)
        assert completed_task is not None

        # Try to claim reward points (might fail due to API restrictions)
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            reward_result = api_client.claim_reward_points(10, task_id, today)
            assert reward_result is not None
        except Exception as e:
            # Reward claiming might not be available for all accounts
            pytest.skip(f"Reward claiming not available: {e}")

    def test_get_kudos_info(self, api_client):
        """Test getting kudos information."""
        kudos = api_client.get_kudos_info()
        assert kudos is not None


class TestErrorHandling:
    """Test error handling in the API client."""

    def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        invalid_client = MarvinAPIClient(api_key="invalid_key")
        with pytest.raises(
            requests.exceptions.HTTPError, match="(400|401) Client Error"
        ):
            invalid_client.get_categories()

    def test_invalid_task_id(self, api_client):
        """Test behavior with invalid task ID."""
        with pytest.raises(requests.exceptions.HTTPError, match="4"):  # 4xx error
            api_client.mark_task_done("invalid_task_id")

    def test_invalid_project_id(self, api_client):
        """Test behavior with invalid project ID."""
        children = api_client.get_children("invalid_project_id")
        # Should return empty list due to error handling
        assert isinstance(children, list)


class TestProjectPlanningEnhancements:
    """Test the new project planning enhancement features."""

    def test_create_project_with_tasks(self, test_project_data):
        """Test creating a project with multiple tasks at once."""

        # Use test data
        api_client = create_api_client()
        task_titles = [f"Test Task {i+1}" for i in range(TASK_COUNT)]
        result = create_project_with_tasks(
            api_client,
            project_title=test_project_data["title"],
            task_titles=task_titles,
        )

        assert result["created_project"] is not None
        assert result["task_count"] == TASK_COUNT
        assert len(result["created_tasks"]) == TASK_COUNT

    def test_get_daily_focus(self):
        """Test getting daily focus items."""

        api_client = create_api_client()
        result = get_daily_focus(api_client)

        assert "total_focus_items" in result
        assert "completed_today" in result
        assert "pending_items" in result
        assert "high_priority_items" in result
        assert "projects" in result
        assert "tasks" in result

    def test_get_productivity_summary(self):
        """Test getting productivity summary."""

        api_client = create_api_client()
        result = get_productivity_summary(api_client)

        assert "date" in result
        assert "active_goals" in result
        assert "summary" in result

    def test_quick_daily_planning(self):
        """Test quick daily planning feature."""

        api_client = create_api_client()
        result = quick_daily_planning(api_client)

        assert "planning_date" in result
        assert "overdue_items" in result
        assert "scheduled_today" in result
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    def test_batch_create_tasks(self):
        """Test batch task creation."""

        # Create test tasks
        api_client = create_api_client()
        tasks = ["Test Task 1", "Test Task 2", "Test Task 3"]
        result = batch_create_tasks(api_client, tasks)

        assert "created_tasks" in result
        assert "failed_tasks" in result
        assert "success_count" in result
        assert result["success_count"] >= 0
        assert result["total_requested"] == TASK_COUNT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
