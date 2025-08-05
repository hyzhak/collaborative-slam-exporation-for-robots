import os
import pytest
import redis
import time
import uuid

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_STREAM = "mission:commands"
GROUP_NAME = "orchestrator_group_integration_test"


@pytest.mark.parametrize("backend", ["celery", "async"])
def test_orchestrator_trigger(redis_client, backend):
    # Ensure group exists for mission:commands
    try:
        redis_client.xgroup_create(REDIS_STREAM, GROUP_NAME, id="$", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    # Ensure groups exist for all downstream streams
    downstreams = [
        ("resources:commands", "resources:allocate"),
        ("routing:commands", "routing:plan"),
        ("exploration:commands", "exploration:perform"),
        ("map:commands", "map:integrate"),
        # TODO: we don't have a release_resources command yet, but we can add it later
        # ("resources:commands",  "resources:release"),
    ]

    for stream, _ in set(downstreams):
        try:
            redis_client.xgroup_create(stream, GROUP_NAME, id="$", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    # Add a test message to the stream with correlation_id
    correlation_id = f"test-correlation-{uuid.uuid4().hex}"
    msg_id = redis_client.xadd(
        REDIS_STREAM,
        {
            "robot_count": 2,
            "area": "ZoneA",
            "correlation_id": correlation_id,
            "event_type": "mission:start",
            "reply_stream": f"mission:replies:{correlation_id}",
            "backend": backend,
        },
    )

    time.sleep(60)

    # Wait for orchestrator to process and emit all expected events in order
    for stream, expected_event in downstreams:
        downstream_msgs = redis_client.xreadgroup(
            GROUP_NAME, "integration_test_consumer", {stream: ">"}, count=1, block=10000
        )
        assert downstream_msgs, f"No message found in downstream stream {stream}"
        assert len(downstream_msgs) == 1, (
            f"Expected one message in {stream}, got {len(downstream_msgs)}"
        )
        stream_name, messages = downstream_msgs[0]
        assert len(messages) == 1, f"Expected one message in {stream_name}, got {len(messages)}"
        msg_id, fields = messages[0]
        assert fields.get("event_type") == expected_event, (
            f"Unexpected event_type: {fields.get('event_type')} (expected: {expected_event})"
        )
        assert "saga_id" in fields, "saga_id missing in downstream event"
        assert fields.get("correlation_id") == correlation_id, (
            f"correlation_id mismatch: {fields.get('correlation_id')} (expected: {correlation_id})"
        )
        redis_client.xack(stream, GROUP_NAME, msg_id)

    # Wait for orchestrator to ACK the message (pending should be 0)
    max_wait = 10  # seconds
    interval = 0.5
    waited = 0
    while waited < max_wait:
        pending = redis_client.xpending(REDIS_STREAM, GROUP_NAME)
        if pending["pending"] == 0:
            break
        time.sleep(interval)
        waited += interval
    assert pending["pending"] == 0, (
        f"Orchestrator did not process the message. "
        f"Expected 0 pending, got {pending['pending']} (stream: {REDIS_STREAM})"
    )
