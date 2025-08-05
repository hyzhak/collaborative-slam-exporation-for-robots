import asyncio
import uuid
import logging

from app.redis_utils.replies import request_and_reply

logger = logging.getLogger(__name__)


async def compensate_allocate_resources(saga_id, correlation_id, **ctx):
    """Async compensation for allocate_resources step."""
    logger.info(
        f"Saga[{saga_id}]: Compensating allocate_resources (correlation_id={correlation_id})"
    )
    return {"compensated": True, "correlation_id": correlation_id}


async def compensate_plan_route(saga_id, correlation_id, **ctx):
    """Async compensation for plan_route step."""
    logger.info(
        f"Saga[{saga_id}]: Compensating plan_route (correlation_id={correlation_id})"
    )
    return {"compensated": True, "correlation_id": correlation_id}


async def compensate_perform_exploration(saga_id, correlation_id, **ctx):
    """Async compensation for perform_exploration step."""
    logger.info(
        f"Saga[{saga_id}]: Aborting exploration (correlation_id={correlation_id})"
    )
    return {"aborted": True, "correlation_id": correlation_id}


async def compensate_integrate_maps(saga_id, correlation_id, **ctx):
    """Async compensation for integrate_maps step."""
    logger.info(
        f"Saga[{saga_id}]: Rolling back map integration (correlation_id={correlation_id})"
    )
    return {"rolled_back": True, "correlation_id": correlation_id}


async def compensate_release_resources(saga_id, correlation_id, **ctx):
    """Async compensation for release_resources step."""
    logger.info(
        f"Saga[{saga_id}]: Releasing allocated robots (correlation_id={correlation_id})"
    )
    return {"released": True, "correlation_id": correlation_id}


async def run_saga(robot_count, area, correlation_id, fail_steps=None):
    """
    Run the mission start saga as a pure-async workflow.
    Sequentially awaits request_and_reply for each step.
    On failure, triggers inline compensation in reverse order.
    """
    saga_id = str(uuid.uuid4())[:8]
    completed_steps = []
    try:
        logger.info(
            f"Saga[{saga_id}]: Allocating {robot_count} robots (correlation_id={correlation_id})"
        )
        await request_and_reply(
            command_stream="resources:commands",
            response_prefix="resources:replies",
            correlation_id=correlation_id,
            saga_id=saga_id,
            event_type="resources:allocate",
            payload={"robots_allocated": robot_count},
            timeout=3,
        )
        completed_steps.append("allocate_resources")

        logger.info(
            f"Saga[{saga_id}]: Planning route for area {area} (correlation_id={correlation_id})"
        )
        await request_and_reply(
            command_stream="routing:commands",
            response_prefix="routing:replies",
            correlation_id=correlation_id,
            saga_id=saga_id,
            event_type="routing:plan",
            payload={"route": f"Route for {area}"},
        )
        completed_steps.append("plan_route")

        logger.info(
            f"Saga[{saga_id}]: Performing exploration with {robot_count} robots (correlation_id={correlation_id})"
        )
        await request_and_reply(
            command_stream="exploration:commands",
            response_prefix="exploration:replies",
            correlation_id=correlation_id,
            saga_id=saga_id,
            event_type="exploration:perform",
            payload={"exploration_result": "success"},
        )
        completed_steps.append("perform_exploration")

        logger.info(
            f"Saga[{saga_id}]: Integrating maps (correlation_id={correlation_id})"
        )
        await request_and_reply(
            command_stream="map:commands",
            response_prefix="map:replies",
            correlation_id=correlation_id,
            saga_id=saga_id,
            event_type="map:integrate",
            payload={"final_map": "integrated_map"},
        )
        completed_steps.append("integrate_maps")

        logger.info(
            f"Saga[{saga_id}]: Releasing allocated robots (correlation_id={correlation_id})"
        )
        await request_and_reply(
            command_stream="release_resources",
            response_prefix="release_resources_reply",
            correlation_id=correlation_id,
            saga_id=saga_id,
            event_type="release_resources",
            payload={},
        )
        completed_steps.append("release_resources")

    except Exception:
        # Inline compensation in reverse order
        for step in reversed(completed_steps):
            if step == "release_resources":
                await compensate_release_resources(saga_id, correlation_id)
            elif step == "integrate_maps":
                await compensate_integrate_maps(saga_id, correlation_id)
            elif step == "perform_exploration":
                await compensate_perform_exploration(saga_id, correlation_id)
            elif step == "plan_route":
                await compensate_plan_route(saga_id, correlation_id)
            elif step == "allocate_resources":
                await compensate_allocate_resources(saga_id, correlation_id)
        raise
