import app.command_handlers.handlers.allocate_resources as handler


def test_handler_interface():
    assert hasattr(handler, "STREAM_NAME")
    assert handler.STREAM_NAME == "resources:commands"
    assert hasattr(handler, "GROUP_NAME")
    assert handler.GROUP_NAME == "resources_handler_group"
    assert hasattr(handler, "EVENT_TYPE")
    assert handler.EVENT_TYPE == "resources:allocate"
    assert hasattr(handler, "handle")
    assert callable(handler.handle)
