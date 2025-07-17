import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.command_listener import run_command_listeners


@pytest.mark.asyncio
async def test_run_command_listeners_invokes_handlers(monkeypatch):
    # Mock handler
    async def mock_handle(fields):
        mock_handle.called = True
        mock_handle.fields = fields

    mock_handle.called = False

    # Mock discovery_handler_modules to return one handler
    monkeypatch.setattr(
        "app.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "allocate_resources",
                "stream": "stream1",
                "group": "group1",
                "handle": mock_handle,
            }
        ],
    )

    # Mock Redis client
    redis_client = MagicMock()
    # Simulate one message, then empty
    redis_client.xread_group = AsyncMock(
        side_effect=[{"stream1": [("msgid1", {"foo": "bar"})]}, {"stream1": []}]
    )
    redis_client.xack = AsyncMock()

    # Run the listener for a short time
    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Assert handler was called
    assert mock_handle.called
    assert mock_handle.fields == {"foo": "bar"}
    redis_client.xack.assert_awaited_with("stream1", "group1", "msgid1")


@pytest.mark.asyncio
async def test_run_command_listeners_handles_errors(monkeypatch):
    # Handler that raises
    async def error_handle(fields):
        raise ValueError("fail")

    monkeypatch.setattr(
        "app.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "error_handler",
                "stream": "stream2",
                "group": "group2",
                "handle": error_handle,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xread_group = AsyncMock(
        side_effect=[{"stream2": [("msgid2", {"baz": "qux"})]}, {"stream2": []}]
    )
    redis_client.xack = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # xack should not be called since handler failed
    redis_client.xack.assert_not_awaited()
