import sys
import types
import pytest
from app.commands.listener import discovery_handler_modules


@pytest.fixture(autouse=True)
def mock_handlers(monkeypatch):
    # Create a dummy app.commands.handlers package
    handlers_pkg = types.ModuleType("app.commands.handlers")
    handlers_pkg.__path__ = []
    sys.modules["app.commands.handlers"] = handlers_pkg

    # Create a dummy handler module
    dummy = types.ModuleType("app.commands.handlers.dummy_handler")
    dummy.STREAM_NAME = "dummy:commands"
    dummy.GROUP_NAME = "dummy_group"
    dummy.handle = lambda fields: None
    dummy.EVENT_TYPE = "dummy:event"
    sys.modules["app.commands.handlers.dummy_handler"] = dummy

    # Patch pkgutil.iter_modules to simulate discovery with ModuleInfo
    from pkgutil import ModuleInfo

    def iter_modules(path):
        return [ModuleInfo(None, "dummy_handler", False)]

    import pkgutil

    monkeypatch.setattr(pkgutil, "iter_modules", iter_modules)


def test_discovery_handler_modules_returns_metadata():
    handlers = discovery_handler_modules()
    assert isinstance(handlers, list)
    assert handlers, "No handlers discovered"
    handler = handlers[0]
    assert handler["name"] == "dummy_handler"
    assert handler["stream"] == "dummy:commands"
    assert handler["group"] == "dummy_group"
    assert handler["event_type"] == "dummy:event"
    assert callable(handler["handle"])
