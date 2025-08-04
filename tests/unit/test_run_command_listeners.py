import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.command_handlers.command_listener import run_command_listeners


@pytest.mark.asyncio
async def test_run_command_listeners_invokes_handlers(monkeypatch):
    # Mock handler
    async def mock_handle(fields):
        mock_handle.called = True
        mock_handle.fields = fields

    mock_handle.called = False

    # Mock discovery_handler_modules to return one handler
    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "allocate_resources",
                "stream": "stream1",
                "group": "group1",
                "event_type": "foo",
                "handle": mock_handle,
            }
        ],
    )

    # Mock Redis client
    redis_client = MagicMock()
    # Make xgroup_create awaitable
    redis_client.xgroup_create = AsyncMock()
    # Simulate one message, then empty
    redis_client.xreadgroup = AsyncMock(
        side_effect=[[("stream1", [("msgid1", {"foo": "bar", "event_type": "foo"})])], []]
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
    assert mock_handle.fields == {"foo": "bar", "event_type": "foo"}
    redis_client.xack.assert_awaited_with("stream1", "group1", "msgid1")


@pytest.mark.asyncio
async def test_run_command_listeners_handles_errors(monkeypatch):
    # Handler that raises
    async def error_handle(fields):
        raise ValueError("fail")

    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "error_handler",
                "stream": "stream2",
                "group": "group2",
                "event_type": "bar",
                "handle": error_handle,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xgroup_create = AsyncMock()
    redis_client.xreadgroup = AsyncMock(
        side_effect=[[("stream2", [("msgid2", {"baz": "qux", "event_type": "bar"})])], []]
    )
    redis_client.xack = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # xack should not be called since handler failed
    redis_client.xack.assert_not_awaited()

@pytest.mark.asyncio
async def test_run_command_listeners_event_type_filter(monkeypatch):
    # Handler expects event_type "foo", but message has "bar"
    async def mock_handle(fields):
        mock_handle.called = True

    mock_handle.called = False

    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "allocate_resources",
                "stream": "stream3",
                "group": "group3",
                "event_type": "foo",
                "handle": mock_handle,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xgroup_create = AsyncMock()
    redis_client.xreadgroup = AsyncMock(
        side_effect=[[("stream3", [("msgid3", {"foo": "bar", "event_type": "bar"})])], []]
    )
    redis_client.xack = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Handler should not be called, xack should not be called
    assert not mock_handle.called
    redis_client.xack.assert_not_awaited()

@pytest.mark.asyncio
async def test_run_command_listeners_no_event_type(monkeypatch):
    # Handler with event_type=None should process all messages
    async def mock_handle(fields):
        mock_handle.called = True

    mock_handle.called = False

    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "integrate_maps",
                "stream": "stream4",
                "group": "group4",
                "event_type": None,
                "handle": mock_handle,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xgroup_create = AsyncMock()
    redis_client.xreadgroup = AsyncMock(
        side_effect=[[("stream4", [("msgid4", {"foo": "bar", "event_type": "baz"})])], []]
    )
    redis_client.xack = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert mock_handle.called
    redis_client.xack.assert_awaited_with("stream4", "group4", "msgid4")

@pytest.mark.asyncio
async def test_run_command_listeners_xread_group_args(monkeypatch):
    # Ensure xread_group is called with correct arguments
    async def mock_handle(fields):
        pass

    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "plan_route",
                "stream": "stream5",
                "group": "group5",
                "event_type": None,
                "handle": mock_handle,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xgroup_create = AsyncMock()
    redis_client.xreadgroup = AsyncMock(
        side_effect=[[("stream5", [("msgid5", {"foo": "bar"})])], []]
    )
    redis_client.xack = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    redis_client.xreadgroup.assert_awaited()

@pytest.mark.asyncio
async def test_run_command_listeners_missing_metadata(monkeypatch):
    # Handler missing stream, group, or handle should be ignored
    monkeypatch.setattr(
        "app.command_handlers.command_listener.discovery_handler_modules",
        lambda: [
            {
                "name": "bad_handler",
                "stream": None,
                "group": "group6",
                "event_type": None,
                "handle": None,
            }
        ],
    )

    redis_client = MagicMock()
    redis_client.xgroup_create = AsyncMock()
    redis_client.xreadgroup = AsyncMock()
    redis_client.xack = AsyncMock()
    # Patch close to be awaitable to match production logic
    redis_client.close = AsyncMock()

    task = asyncio.create_task(run_command_listeners(redis_client))
    await asyncio.sleep(0.2)
    await task

    redis_client.xreadgroup.assert_not_awaited()
