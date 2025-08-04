import asyncio
import logging

from app.celery_app import celery_app
from app.logging_config import setup_logging
from app.redis_utils import request_and_reply


setup_logging()
logger = logging.getLogger(__name__)


@celery_app.task
def allocate_resources(correlation_id, saga_id, robot_count):
    logger.info(
        f"Saga[{saga_id}]: Allocating {robot_count} robots (correlation_id={correlation_id})"
    )
    try:
        result = asyncio.run(
            request_and_reply(
                "resources:commands",
                "resources:replies",
                correlation_id,
                saga_id,
                "resources:allocate",
                {"robots_allocated": robot_count},
                timeout=3,
            )
        )
        return result
    except Exception as e:
        logger.error(f"RuntimeError in allocate_resources: {e}")
        raise



@celery_app.task
def plan_route(correlation_id, saga_id, area):
    logger.info(
        f"Saga[{saga_id}]: Planning route for area {area} (correlation_id={correlation_id})"
    )
    return asyncio.run(
        request_and_reply(
            "routing:commands",
            "routing:replies",
            correlation_id,
            saga_id,
            "routing:plan",
            {"route": f"Route for {area}"},
        )
    )


@celery_app.task
def perform_exploration(correlation_id, saga_id, robot_count):
    logger.info(
        f"Saga[{saga_id}]: Performing exploration with {robot_count} robots (correlation_id={correlation_id})"
    )
    return asyncio.run(
        request_and_reply(
            "exploration:commands",
            "exploration:replies",
            correlation_id,
            saga_id,
            "exploration:perform",
            {"exploration_result": "success"},
        )
    )


@celery_app.task
def integrate_maps(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Integrating maps (correlation_id={correlation_id})")
    return asyncio.run(
        request_and_reply(
            "map:commands",
            "map:replies",
            correlation_id,
            saga_id,
            "map:integrate",
            {"final_map": "integrated_map"},
        )
    )


# Compensation tasks


@celery_app.task
def release_resources(correlation_id, saga_id):
    logger.info(
        f"Saga[{saga_id}]: Releasing allocated robots (correlation_id={correlation_id})"
    )
    return {"released": True, "correlation_id": correlation_id}


@celery_app.task
def abort_exploration(correlation_id, saga_id):
    logger.info(
        f"Saga[{saga_id}]: Aborting exploration (correlation_id={correlation_id})"
    )
    return {"aborted": True, "correlation_id": correlation_id}


@celery_app.task
def rollback_integration(correlation_id, saga_id):
    logger.info(
        f"Saga[{saga_id}]: Rolling back map integration (correlation_id={correlation_id})"
    )
    return {"rolled_back": True, "correlation_id": correlation_id}
