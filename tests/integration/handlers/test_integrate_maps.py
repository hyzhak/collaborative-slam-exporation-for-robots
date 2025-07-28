import pytest
from tests.integration.handlers.utils import redis_client, send_command, collect_events, generate_ids

STREAM = "map:commands"
REPLY_STREAM = f"{STREAM}:replies"
GROUP = f"{STREAM}:integration_test_group"
CONSUMER = "integration_test_consumer"

@pytest.fixture(scope="function", autouse=True)
def setup_consumer_group(redis_client):
    try:
        redis_client.xgroup_create(f"{STREAM}:replies", GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise

def test_integrate_maps_reply_sequence(redis_client):
    correlation_id, saga_id = generate_ids()
    command_data = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": "map:integrate",
        "payload": '{"maps": ["mapA", "mapB"], "zone": "A"}',
        "reply_stream": REPLY_STREAM,
    }
    events = collect_events(redis_client, REPLY_STREAM, GROUP, CONSUMER, correlation_id, timeout=10.0)
    assert not events, f"Expected no events before sending command, but got: {events}"
    send_command(redis_client, STREAM, command_data)
    events = collect_events(redis_client, REPLY_STREAM, GROUP, CONSUMER, correlation_id, timeout=10.0)
    assert events == ["start", "progress", "completed"]
