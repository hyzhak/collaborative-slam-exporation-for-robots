import sys
import importlib
from types import ModuleType


def test_allocate_resources_reply_handling(monkeypatch):
    # Inject dummy celery_app before importing app.tasks
    class DummyTask:
        def task(self, fn):
            return fn
    celery_mod = ModuleType("app.celery_app")
    celery_mod.celery_app = DummyTask()
    sys.modules["app.celery_app"] = celery_mod
    tasks = importlib.import_module("app.tasks")

    # Patch request_and_reply and run
    fake_resp = {"robots_allocated": 3}
    monkeypatch.setattr(tasks, "request_and_reply", lambda *args, **kwargs: fake_resp)
    result = tasks.allocate_resources("cid", "sid", 3)

    assert result == fake_resp
