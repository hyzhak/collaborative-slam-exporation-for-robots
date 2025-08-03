import asyncio
import uuid
import logging
from celery import chain
from app.tasks import (
    allocate_resources,
    plan_route,
    perform_exploration,
    integrate_maps,
    release_resources,
    abort_exploration,
    rollback_integration,
)
from app.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


async def run_saga(robot_count, area, correlation_id, fail_steps=None):
    """
    fail_steps: optional set/list of step names to force failure for testing, e.g. {"allocate_resources"}
    correlation_id: required, must be passed from orchestrator_listener
    """
    saga_id = str(uuid.uuid4())[:8]
    fail_steps = set(fail_steps or [])
    logger.info(
        f"Saga[{saga_id}]: Starting saga with {robot_count} robots in area '{area}', correlation_id={correlation_id}"
    )

    # Build the main saga chain using Celery Canvas with compensation via link_error
    # All tasks must receive correlation_id and saga_id as first arguments
    allocate = allocate_resources.s(correlation_id, saga_id, robot_count).set(
        link_error=release_resources.si(correlation_id, saga_id)
    )
    plan = plan_route.si(correlation_id, saga_id, area).set(
        link_error=release_resources.si(correlation_id, saga_id)
    )
    explore = perform_exploration.si(correlation_id, saga_id, robot_count).set(
        link_error=chain(
            abort_exploration.si(correlation_id, saga_id),
            release_resources.si(correlation_id, saga_id)
        )
    )
    integrate = integrate_maps.si(correlation_id, saga_id).set(
        link_error=chain(
            rollback_integration.si(correlation_id, saga_id),
            abort_exploration.si(correlation_id, saga_id),
            release_resources.si(correlation_id, saga_id)
        )
    )
    saga_chain = chain(
        allocate,
        plan,
        explore,
        integrate,
        release_resources.si(correlation_id, saga_id)
    )

    logger.info(f"Saga[{saga_id}]: Canvas chain dispatched with compensation.")
    result = await asyncio.to_thread(saga_chain.apply_async, expires=1000)
    logger.info(f"Saga[{saga_id}]: Saga dispatched, Celery job is {result}")
    return result
