import sys
import importlib
from types import ModuleType
import pytest


def _mock_celery():
    class DummyTask:
        def task(self, fn):
            return fn

    celery_mod = ModuleType("app.celery_app")
    celery_mod.celery_app = DummyTask()
    sys.modules["app.celery_app"] = celery_mod


@pytest.fixture(autouse=True)
def disable_celery_registration():
    _mock_celery()


@pytest.mark.parametrize(
    "task_name, args, fake_response",
    [
        ("allocate_resources", ("cid", "sid", 3), {"robots_allocated": 3}),
        ("plan_route", ("cid", "sid", "AreaX"), {"route": "Route for AreaX"}),
        ("perform_exploration", ("cid", "sid", 2), {"exploration_result": "success"}),
        ("integrate_maps", ("cid", "sid"), {"final_map": "integrated_map"}),
    ],
)
def test_request_reply_tasks(monkeypatch, task_name, args, fake_response):
    # Import tasks after Celery is mocked
    tasks = importlib.import_module("app.flows.mission_start_celery.tasks")

    # Patch the request_and_reply helper to return a coroutine that yields fake_response
    async def fake_coro(*a, **k):
        return fake_response
    monkeypatch.setattr(tasks, "request_and_reply", fake_coro)

    # Invoke the task function
    fn = getattr(tasks, task_name)
    result = fn(*args)

    assert result == fake_response
