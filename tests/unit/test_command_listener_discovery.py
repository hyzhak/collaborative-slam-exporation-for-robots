import sys
import types
import pytest
from app.command_listener import discovery_handler_modules


@pytest.fixture(autouse=True)
def mock_handlers(monkeypatch):
    # Create a dummy app.handlers package
    handlers_pkg = types.ModuleType("app.handlers")
    handlers_pkg.__path__ = []
    sys.modules["app.handlers"] = handlers_pkg

    # Create a dummy handler module
    dummy = types.ModuleType("app.handlers.dummy_handler")
    dummy.STREAM_NAME = "dummy:commands"
    dummy.GROUP_NAME = "dummy_group"
    dummy.handle = lambda fields: None
    sys.modules["app.handlers.dummy_handler"] = dummy

    # Patch pkgutil.iter_modules to simulate discovery
    def iter_modules(path):
        return [("dummy_handler", False)]

    monkeypatch.setattr("pkgutil.iter_modules", lambda path: iter_modules(path))


def test_discovery_handler_modules_returns_metadata():
    handlers = discovery_handler_modules()
    assert isinstance(handlers, list)
    assert handlers, "No handlers discovered"
    handler = handlers[0]
    assert handler["name"] == "dummy_handler"
    assert handler["stream"] == "dummy:commands"
    assert handler["group"] == "dummy_group"
    assert callable(handler["handle"])
