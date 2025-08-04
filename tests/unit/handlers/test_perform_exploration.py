import pytest
from unittest.mock import patch
import app.commands.handlers.perform_exploration as handler


@pytest.mark.asyncio
async def test_handler_emits_multi_stage_events():
    fields = {
        "stream": "exploration:commands",
        "reply_stream": "exploration:replies:cid",
        "correlation_id": "cid",
        "saga_id": "sid",
        "event_type": "exploration:perform"
    }
    with patch("app.redis_utils.decorators.emit_event") as mock_emit:
        with patch("app.redis_utils.commands.get_redis_client"):
            await handler.handle(fields)
        statuses = [call.kwargs.get("status") for call in mock_emit.call_args_list]
        streams = [call.kwargs.get("stream") for call in mock_emit.call_args_list]
        assert streams[0] == "exploration:replies:cid"
        assert statuses[0] == "start"
        assert "progress" in statuses
        assert statuses[-1] == "completed"
