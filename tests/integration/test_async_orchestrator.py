import pytest
import uuid
import app.flows.mission_start_async.orchestrator as async_orch

@pytest.mark.asyncio
async def test_async_orchestrator_success_path():
    """
    All steps succeed, no compensation triggered.
    """
    robot_count = 2
    area = "ZoneA"
    correlation_id = str(uuid.uuid4())
    # TODO: Call run_saga and assert expected events
    await async_orch.run_saga(robot_count, area, correlation_id)

@pytest.mark.asyncio
async def test_async_orchestrator_failure_triggers_compensation():
    """
    Simulate failure in a step and assert compensation is called in reverse order.
    """
    robot_count = 2
    area = "ZoneA"
    correlation_id = str(uuid.uuid4())
    fail_steps = ["plan_route"]
    # TODO: Call run_saga with fail_steps and assert compensation
    await async_orch.run_saga(robot_count, area, correlation_id, fail_steps=fail_steps)
