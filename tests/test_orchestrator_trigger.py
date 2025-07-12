import os
import time
import redis
import pytest

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_STREAM = os.environ.get("REDIS_STREAM", "saga_requests")
GROUP_NAME = "orchestrator_group"


@pytest.fixture(scope="module")
def redis_client():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield r


def test_orchestrator_trigger(redis_client):
    # Ensure group exists
    try:
        redis_client.xgroup_create(REDIS_STREAM, GROUP_NAME, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    # Add a test message to the stream
    msg_id = redis_client.xadd(REDIS_STREAM, {"robot_count": 2, "area": "ZoneA"})
    time.sleep(10)  # Give orchestrator time to process

    # Check if message is pending (should be 0 if ACKed)
    pending = redis_client.xpending(REDIS_STREAM, GROUP_NAME)
    assert pending["pending"] == 0, f"Expected 0 pending, got {pending['pending']}"
