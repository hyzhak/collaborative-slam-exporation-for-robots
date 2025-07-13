import os
import time
import redis
import pytest

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_STREAM = os.environ.get("REDIS_STREAM", "mission:commands")
GROUP_NAME = "orchestrator_group"


@pytest.fixture(scope="module")
def redis_client():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield r


def test_orchestrator_trigger(redis_client):
    # Ensure group exists for mission:commands
    try:
        redis_client.xgroup_create(REDIS_STREAM, GROUP_NAME, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    # Ensure group exists for downstream stream
    downstream_stream = "resources:commands"
    try:
        redis_client.xgroup_create(downstream_stream, GROUP_NAME, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    # Add a test message to the stream with correlation_id
    msg_id = redis_client.xadd(
        REDIS_STREAM,
        {"robot_count": 2, "area": "ZoneA", "correlation_id": "test-correlation-123"}
    )
    time.sleep(5)  # Give orchestrator time to process

    # Check if message is pending (should be 0 if ACKed)
    pending = redis_client.xpending(REDIS_STREAM, GROUP_NAME)
    assert pending["pending"] == 0, (
        f"Orchestrator did not process the message. "
        f"Expected 0 pending, got {pending['pending']} (stream: {REDIS_STREAM})"
    )

    # Use consumer group to read the new event from downstream stream
    downstream_msgs = redis_client.xreadgroup(GROUP_NAME, "test_consumer", {downstream_stream: ">"}, count=1, block=5000)
    assert downstream_msgs, f"No message found in downstream stream {downstream_stream}"
    stream_name, messages = downstream_msgs[0]
    msg_id, fields = messages[0]
    assert fields.get("event_type") == "resources:allocate", f"Unexpected event_type: {fields.get('event_type')}"
    assert "saga_id" in fields, "saga_id missing in downstream event"
    assert fields.get("correlation_id") == "test-correlation-123", f"correlation_id mismatch: {fields.get('correlation_id')}"
