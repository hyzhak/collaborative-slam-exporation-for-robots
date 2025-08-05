import pytest
import uuid
import app.flows.mission_start_async.orchestrator as async_orch


@pytest.mark.asyncio
async def test_run_saga_exists(monkeypatch):
    """run_saga should be defined and awaitable, with request_and_reply mocked and step order validated."""
    robot_count = 1
    area = "TestArea"
    correlation_id = str(uuid.uuid4())

    steps = []

    async def fake_request_and_reply(*a, **kw):
        steps.append(kw.get("event_type"))
        return {"status": "ok"}

    monkeypatch.setattr(async_orch, "request_and_reply", fake_request_and_reply)
    result = await async_orch.run_saga(robot_count, area, correlation_id)
    assert result is None
    assert steps == [
        "resources:allocate",
        "routing:plan",
        "exploration:perform",
        "map:integrate",
        "release_resources",
    ]


@pytest.mark.asyncio
async def test_compensation_functions_exist():
    """Compensation functions should be defined and awaitable."""
    saga_id = "testid"
    correlation_id = "cid"
    for fn in [
        async_orch.compensate_allocate_resources,
        async_orch.compensate_plan_route,
        async_orch.compensate_perform_exploration,
        async_orch.compensate_integrate_maps,
        async_orch.compensate_release_resources,
    ]:
        result = await fn(saga_id, correlation_id)
        assert isinstance(result, dict)
        assert "correlation_id" in result
