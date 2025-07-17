import pytest
import requests


def test_redisinsight_accessible():
    """
    Integration test: RedisInsight UI should be accessible on port 5540.
    """
    url = "http://redisinsight:5540"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        pytest.fail(f"Could not connect to RedisInsight at {url}: {e}")
    assert resp.status_code == 200 or resp.status_code == 302, (
        f"Unexpected status code: {resp.status_code}"
    )
