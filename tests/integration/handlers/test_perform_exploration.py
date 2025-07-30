import pytest
from tests.integration.handlers.utils import (
    collect_events,
    ids_mock,
    redis_client,
    send_command,
)

STREAM = "exploration:commands"
STREAM_REPLAY_PREFIX = "exploration:replies"
GROUP = f"{STREAM}:integration_test_group"
CONSUMER = "integration_test_consumer"

@pytest.fixture(scope="function", autouse=True)
def replay_stream_mock(ids_mock):
    correlation_id, saga_id = ids_mock
    return f"{STREAM_REPLAY_PREFIX}:{correlation_id}"

@pytest.fixture(scope="function", autouse=True)
def setup_consumer_group(redis_client, replay_stream_mock):
    try:
        redis_client.xgroup_create(replay_stream_mock, GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise

def test_perform_exploration_reply_sequence(redis_client, replay_stream_mock, ids_mock):
    correlation_id, saga_id = ids_mock
    command_data = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": "exploration:perform",
        "payload": '{"area": "ZoneC", "robots": ["r1", "r2"]}',
        "reply_stream": replay_stream_mock,
    }
    events = collect_events(redis_client, replay_stream_mock, GROUP, CONSUMER, correlation_id, timeout=10.0)
    assert not events, f"Expected no events before sending command, but got: {events}"
    send_command(redis_client, STREAM, command_data)
    events = collect_events(redis_client, replay_stream_mock, GROUP, CONSUMER, correlation_id, timeout=10.0)
    assert events == ["start", "progress", "completed"]
