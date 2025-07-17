import pytest
import app.handlers.allocate_resources as handler

def test_handler_interface():
    assert hasattr(handler, "STREAM_NAME")
    assert handler.STREAM_NAME == "resources:commands"
    assert hasattr(handler, "GROUP_NAME")
    assert handler.GROUP_NAME == "resources_handler_group"
    assert hasattr(handler, "handle")
    assert callable(handler.handle)

def test_handle_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        handler.handle({})
