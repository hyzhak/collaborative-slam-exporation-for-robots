import os
import uuid
import pytest
import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

@pytest.fixture(scope="session")
def redis_client():
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    yield client
    client.close()

def generate_ids():
    """
    Generate unique correlation_id and saga_id.
    """
    return str(uuid.uuid4()), str(uuid.uuid4())

@pytest.fixture(scope="function", autouse=True)
def ids_mock():
    """
    Fixture to generate a unique correlation ID for each test.
    """
    return generate_ids()
