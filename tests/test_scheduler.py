import time
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from core.scheduler import ScheduledTask, load_tasks, run_task


def test_scheduled_task_creation():
    task = ScheduledTask("test", "0 8 * * *", "hello", 123)
    assert task.name == "test"
    assert task.next_run > time.time() - 1


def test_scheduled_task_is_due():
    task = ScheduledTask("test", "* * * * *", "hello", 123)
    # A "every minute" cron should be due very soon
    task.next_run = time.time() - 1
    assert task.is_due() is True


def test_scheduled_task_not_due():
    task = ScheduledTask("test", "0 8 * * *", "hello", 123)
    task.next_run = time.time() + 3600
    assert task.is_due() is False


def test_scheduled_task_advance():
    task = ScheduledTask("test", "0 * * * *", "hello", 123)
    first = task.next_run
    task.advance()
    assert task.next_run > first


def test_load_tasks_valid():
    config = {
        "scheduler": {
            "tasks": [
                {"name": "morning", "cron": "0 8 * * *", "prompt": "hello", "chat_id": 123},
                {"name": "evening", "cron": "0 21 * * *", "prompt": "bye", "chat_id": 123},
            ]
        }
    }
    tasks = load_tasks(config)
    assert len(tasks) == 2
    assert tasks[0].name == "morning"
    assert tasks[1].name == "evening"


def test_load_tasks_empty():
    assert load_tasks({}) == []
    assert load_tasks({"scheduler": {}}) == []
    assert load_tasks({"scheduler": {"tasks": []}}) == []


def test_load_tasks_invalid_skipped():
    config = {
        "scheduler": {
            "tasks": [
                {"name": "valid", "cron": "0 8 * * *", "prompt": "hello", "chat_id": 123},
                {"name": "missing_cron", "prompt": "hello", "chat_id": 123},
            ]
        }
    }
    tasks = load_tasks(config)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_run_task_success():
    from core.bridge import ClaudeResponse
    task = ScheduledTask("test", "* * * * *", "hello", 123)

    mock_lock = AsyncMock()
    mock_lock.__aenter__ = AsyncMock()
    mock_lock.__aexit__ = AsyncMock()

    mock_response = ClaudeResponse(text="Good morning!", session_id="s1")

    with (
        patch("core.scheduler.send_message", new_callable=AsyncMock, return_value=mock_response),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock()

        await run_task(task, "fake_token", "/tmp/bot", mock_lock)

    mock_client.post.assert_called_once()
