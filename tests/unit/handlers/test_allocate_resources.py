import pytest
from unittest.mock import patch, MagicMock
import app.command_handlers.handlers.allocate_resources as handler

def test_handler_emits_multi_stage_events():
    fields = {"stream": "resources:commands", "correlation_id": "cid", "saga_id": "sid", "event_type": "resources:allocate"}
    with patch("app.redis_utils.decorators.emit_event") as mock_emit:
        with patch("app.redis_utils.commands.get_redis_client"):
            handler.handle(fields)
        # Debug: print all call args and kwargs
        for call in mock_emit.call_args_list:
            print("emit_event call:", call)
        # status is passed as a keyword argument
        statuses = [call.kwargs.get("status") for call in mock_emit.call_args_list]
        assert statuses[0] == "start"
        assert "progress" in statuses
        assert statuses[-1] == "completed"
