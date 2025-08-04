import pytest
from unittest.mock import patch
import app.commands.handlers.integrate_maps as handler


@pytest.mark.asyncio
async def test_handler_emits_multi_stage_events():
    fields = {
        "stream": "map:commands",
        "reply_stream": "map:replies:cid",
        "correlation_id": "cid",
        "saga_id": "sid",
        "event_type": "map:integrate"
    }
    with patch("app.redis_utils.decorators.emit_event") as mock_emit:
        with patch("app.redis_utils.commands.get_redis_client"):
            await handler.handle(fields)
        statuses = [call.kwargs.get("status") for call in mock_emit.call_args_list]
        streams = [call.kwargs.get("stream") for call in mock_emit.call_args_list]
        assert streams[0] == "map:replies:cid"
        assert statuses[0] == "start"
        assert "progress" in statuses
        assert statuses[-1] == "completed"
