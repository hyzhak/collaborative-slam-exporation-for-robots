import pytest

from app.redis_utils.replies import request_and_reply
from tests.integration.handlers.utils import (
    collect_events,
    send_command,
)

STREAM = "resources:commands"
STREAM_REPLAY_PREFIX = "resources:replies"
GROUP = f"{STREAM}:integration_test_group"
CONSUMER = "integration_test_consumer"


@pytest.fixture(scope="function", autouse=True)
def replay_stream_mock(ids_mock):
    """
    Mock function to generate a reply stream based on correlation ID.
    """
    correlation_id, saga_id = ids_mock
    return f"{STREAM_REPLAY_PREFIX}:{correlation_id}"


@pytest.fixture(scope="function", autouse=True)
def setup_consumer_group(redis_client, replay_stream_mock):
    try:
        redis_client.xgroup_create(replay_stream_mock, GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise


def test_allocate_resources_reply_sequence(redis_client, replay_stream_mock, ids_mock):
    correlation_id, saga_id = ids_mock
    command_data = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": "resources:allocate",
        "payload": '{"resources": ["cpu", "memory"], "zone": "A"}',
        "reply_stream": replay_stream_mock,
    }
    events = collect_events(
        redis_client, replay_stream_mock, GROUP, CONSUMER, correlation_id, timeout=10.0
    )
    assert not events, f"Expected no events before sending command, but got: {events}"
    send_command(redis_client, STREAM, command_data)
    events = collect_events(
        redis_client, replay_stream_mock, GROUP, CONSUMER, correlation_id, timeout=10.0
    )
    assert events == ["start", "progress", "completed"]


@pytest.mark.asyncio
async def test_allocate_resources_request_and_reply_pattern(ids_mock):
    """
    Integration test: verify request_and_reply + multi_stage_reply pattern.
    """

    correlation_id, saga_id = ids_mock
    robot_count = 2
    command_stream = "resources:commands"
    response_prefix = "resources:replies"
    event_type = "resources:allocate"
    payload = {"robots_allocated": robot_count}

    await request_and_reply(
        command_stream,
        response_prefix,
        correlation_id,
        saga_id,
        event_type,
        payload,
        timeout=3,
    )
