import subprocess
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from core.bot import (
    handle_message,
    handle_new,
    handle_usage,
    handle_status,
    handle_help,
    is_authorized,
    _heartbeat,
)
from core.bridge import ClaudeResponse


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 111
    update.effective_chat.id = 111
    update.message.text = "Hello bot"
    update.message.reply_text = AsyncMock()
    update.message.chat.send_action = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.bot.send_message = AsyncMock()
    ctx.bot.send_chat_action = AsyncMock()
    return ctx


def test_is_authorized_allowed():
    assert is_authorized(111, [111, 222]) is True


def test_is_authorized_denied():
    assert is_authorized(999, [111, 222]) is False


@pytest.mark.asyncio
async def test_handle_message_unauthorized(mock_update, mock_context):
    mock_update.effective_user.id = 999
    with patch("core.bot._config", {"telegram": {"allowed_users": [111]}}):
        await handle_message(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    assert "not authorized" in mock_update.message.reply_text.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_message_sends_response(mock_update, mock_context):
    mock_sessions = MagicMock()
    mock_sessions.get_session.return_value = None

    mock_response = ClaudeResponse(
        text="Hi there!", session_id="sess-123", cost_usd=0.001,
        usage={"input_tokens": 10, "output_tokens": 5},
    )

    with (
        patch("core.bot._config", {"telegram": {"allowed_users": [111]}}),
        patch("core.bot._sessions", mock_sessions),
        patch("core.bot.send_message", new_callable=AsyncMock, return_value=mock_response),
    ):
        await handle_message(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once_with("Hi there!")
    mock_sessions.set_session.assert_called_once_with(111, "sess-123")
    mock_sessions.log_usage.assert_called_once()


@pytest.mark.asyncio
async def test_handle_new_clears_session(mock_update, mock_context):
    with (
        patch("core.bot._config", {"telegram": {"allowed_users": [111]}}),
        patch("core.bot._sessions") as mock_sm,
    ):
        await handle_new(mock_update, mock_context)

    mock_sm.clear_session.assert_called_once_with(111)
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_usage(mock_update, mock_context):
    mock_sessions = MagicMock()
    mock_sessions.get_usage.return_value = {
        "today": {"cost_usd": 0.0123, "input_tokens": 5000, "output_tokens": 2000, "messages": 10},
        "total": {"cost_usd": 0.4567, "input_tokens": 150000, "output_tokens": 60000, "messages": 200},
    }

    with (
        patch("core.bot._config", {"telegram": {"allowed_users": [111]}}),
        patch("core.bot._sessions", mock_sessions),
    ):
        await handle_usage(mock_update, mock_context)

    msg = mock_update.message.reply_text.call_args[0][0]
    assert "$0.0123" in msg
    assert "$0.4567" in msg
    assert "10 msgs" in msg
    assert "200 msgs" in msg


@pytest.mark.asyncio
async def test_handle_status(mock_update, mock_context):
    mock_sessions = MagicMock()
    mock_sessions.get_session.return_value = "sess-abc"

    with (
        patch("core.bot._config", {"telegram": {"allowed_users": [111]}}),
        patch("core.bot._sessions", mock_sessions),
    ):
        await handle_status(mock_update, mock_context)

    msg = mock_update.message.reply_text.call_args[0][0]
    assert "sess-abc" in msg


@pytest.mark.asyncio
async def test_heartbeat_pulls(tmp_path):
    mock_result = subprocess.CompletedProcess(
        args=["git", "pull", "--ff-only"],
        returncode=0,
        stdout="Updating abc..def\nFast-forward\n",
        stderr="",
    )

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result):
        import asyncio
        task = asyncio.create_task(_heartbeat(str(tmp_path), interval=0))
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_handle_help(mock_update, mock_context):
    await handle_help(mock_update, mock_context)
    msg = mock_update.message.reply_text.call_args[0][0]
    assert "/new" in msg
    assert "/usage" in msg
    assert "/help" in msg
