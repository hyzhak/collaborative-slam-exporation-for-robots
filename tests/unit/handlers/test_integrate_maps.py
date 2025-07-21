import pytest
from unittest.mock import patch, MagicMock
import app.command_handlers.handlers.integrate_maps as handler

def test_handler_emits_multi_stage_events():
    fields = {"stream": "map:commands", "correlation_id": "cid", "saga_id": "sid", "event_type": "map:integrate"}
    with patch("app.redis_utils.decorators.emit_event") as mock_emit:
        with patch("app.redis_utils.commands.get_redis_client"):
            handler.handle(fields)
        for call in mock_emit.call_args_list:
            print("emit_event call:", call)
        statuses = [call.kwargs.get("status") for call in mock_emit.call_args_list]
        assert statuses[0] == "start"
        assert "progress" in statuses
        assert statuses[-1] == "completed"
