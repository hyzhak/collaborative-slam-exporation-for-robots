import pytest
import time
import logging
from unittest.mock import patch, MagicMock
from app import redis_utils
from app.logging_config import setup_logging

setup_logging("DEBUG")


@pytest.fixture
def mock_redis():
    mock = MagicMock()
    mock.xgroup_create.side_effect = lambda *a, **kw: None
    return mock


def test_immediate_fail_strategy():
    assert redis_utils.immediate_fail_retry(1, 0, 0) is None


def test_exponential_retry_strategy():
    # attempt 1: 0.1, attempt 2: 0.2, attempt 3: 0.4, attempt 4: 0.8 (max 1.0)
    strat = redis_utils.exponential_retry()
    assert pytest.approx(strat(1, 0, 0)) == 0.1
    assert pytest.approx(strat(2, 0, 0)) == 0.2
    assert pytest.approx(strat(3, 0, 0)) == 0.4
    assert pytest.approx(strat(4, 0, 0)) == 0.8
    assert pytest.approx(strat(5, 0, 0)) == 1.0


def test_linear_retry_strategy():
    # attempt 1: 0.2, attempt 2: 0.4, attempt 3: 0.6 (max 1.0)
    strat = redis_utils.linear_retry()
    assert pytest.approx(strat(1, 0, 0)) == 0.2
    assert pytest.approx(strat(2, 0, 0)) == 0.4
    assert pytest.approx(strat(3, 0, 0)) == 0.6
    assert pytest.approx(strat(5, 0, 0)) == 1.0


@patch("app.redis_utils.get_redis_client")
def test_read_replies_immediate_fail(mock_get_client, mock_redis):
    mock_get_client.return_value = mock_redis
    mock_redis.xreadgroup.return_value = []
    with pytest.raises(TimeoutError):
        redis_utils.read_replies(
            "stream",
            "corr",
            "req",
            timeout=1,
            retry_strategy=redis_utils.immediate_fail_retry,
        )


@patch("app.redis_utils.get_redis_client")
@patch("time.sleep", return_value=None)
def test_read_replies_exponential_retry(mock_sleep, mock_get_client, mock_redis):
    mock_get_client.return_value = mock_redis
    # Simulate two empty responses, then one with a completed message
    responses = [
        [("stream", [])],
        [("stream", [])],
        [("stream", [("id3", {"status": "completed", "result": "ok"})])],
    ]
    mock_redis.xreadgroup.side_effect = (
        lambda *a, **kw: responses.pop(0) if responses else []
    )
    retry_strategy = redis_utils.exponential_retry(max_attempts=20)
    result = redis_utils.read_replies(
        "stream", "corr", "req", timeout=2, retry_strategy=retry_strategy
    )
    assert result["status"] == "completed"
    assert result["result"] == "ok"


@patch("app.redis_utils.get_redis_client")
@patch("time.sleep", return_value=None)
def test_read_replies_linear_retry(mock_sleep, mock_get_client, mock_redis):
    mock_get_client.return_value = mock_redis
    responses = [
        [("stream", [("id1", {"status": "start"})])],
        [("stream", [("id2", {"status": "progress"})])],
        [("stream", [("id3", {"status": "completed", "result": "done"})])],
    ]
    mock_redis.xreadgroup.side_effect = (
        lambda *a, **kw: responses.pop(0) if responses else []
    )
    retry_strategy = redis_utils.linear_retry(max_attempts=20)
    with patch.object(logging, "info") as mock_log:
        result = redis_utils.read_replies(
            "stream", "corr", "req", timeout=2, retry_strategy=retry_strategy
        )
        assert result["status"] == "completed"
        assert result["result"] == "done"
        assert mock_log.call_count == 3
        calls = [call.args[0] for call in mock_log.call_args_list]
        assert any("Reply status: start" in msg for msg in calls)
        assert any("Reply status: progress" in msg for msg in calls)
        assert any("completed reply" in msg for msg in calls)


@patch("app.redis_utils.get_redis_client")
@patch("time.sleep", return_value=None)
def test_read_replies_timeout(mock_sleep, mock_get_client, mock_redis):
    mock_get_client.return_value = mock_redis
    mock_redis.xreadgroup.return_value = []
    retry_strategy = redis_utils.exponential_retry()
    with pytest.raises(TimeoutError):
        redis_utils.read_replies(
            "stream",
            "corr",
            "req",
            timeout=0.5,
            retry_strategy=retry_strategy,
        )


def test_emit_command_with_maxlen_ttl():
    mock_redis = MagicMock()
    with patch("app.redis_utils.get_redis_client", return_value=mock_redis):
        redis_utils.emit_command(
            "stream", "corr", "saga", "evt", {"a": 1}, maxlen=100, ttl=60
        )
    mock_redis.xadd.assert_called_once()
    args, kwargs = mock_redis.xadd.call_args
    assert kwargs.get("maxlen") == 100
    assert kwargs.get("approximate") is True
    mock_redis.expire.assert_called_once_with("stream", 60)


def test_emit_event_with_maxlen_ttl():
    mock_redis = MagicMock()
    with patch("app.redis_utils.get_redis_client", return_value=mock_redis):
        redis_utils.emit_event(
            "stream", "corr", "saga", "evt", "status", {"b": 2}, maxlen=50, ttl=30
        )
    mock_redis.xadd.assert_called_once()
    args, kwargs = mock_redis.xadd.call_args
    assert kwargs.get("maxlen") == 50
    assert kwargs.get("approximate") is True
    mock_redis.expire.assert_called_once_with("stream", 30)
