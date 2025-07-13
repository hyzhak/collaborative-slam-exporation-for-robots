from app.logging_config import setup_logging
setup_logging()

import logging
import random
import time
from .celery_app import celery_app
from .redis_utils import emit_command, emit_event

logger = logging.getLogger(__name__)


@celery_app.task
def allocate_resources(correlation_id, saga_id, robot_count, fail=False):
    logger.info(f"Saga[{saga_id}]: Allocating {robot_count} robots (correlation_id={correlation_id})")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Allocation failed!")
        emit_event(
            "mission:events",
            correlation_id,
            saga_id,
            "resources:failed",
            "failed",
            {"error": "Allocation failed"},
        )
        raise Exception("Allocation failed")
    logger.info(f"Saga[{saga_id}]: Successfully allocated robots")
    emit_command(
        "resources:commands",
        correlation_id,
        saga_id,
        "resources:allocate",
        {"robots_allocated": robot_count},
    )
    return {"robots_allocated": robot_count}


@celery_app.task
def plan_route(correlation_id, saga_id, area, fail=False):
    logger.info(f"Saga[{saga_id}]: Planning route for area {area} (correlation_id={correlation_id})")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Route planning failed!")
        emit_event(
            "mission:events",
            correlation_id,
            saga_id,
            "plan:failed",
            "failed",
            {"error": "Route planning failed"},
        )
        raise Exception("Route planning failed")
    logger.info(f"Saga[{saga_id}]: Route planned")
    emit_command(
        "plan:commands",
        correlation_id,
        saga_id,
        "plan:plan",
        {"route": f"Route for {area}"},
    )
    return {"route": f"Route for {area}"}


@celery_app.task
def perform_exploration(correlation_id, saga_id, robot_count, fail=False):
    logger.info(f"Saga[{saga_id}]: Performing exploration with {robot_count} robots (correlation_id={correlation_id})")
    time.sleep(2)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Exploration failed!")
        emit_event(
            "mission:events",
            correlation_id,
            saga_id,
            "exploration:failed",
            "failed",
            {"error": "Exploration failed"},
        )
        raise Exception("Exploration failed")
    logger.info(f"Saga[{saga_id}]: Exploration complete")
    emit_command(
        "exploration:commands",
        correlation_id,
        saga_id,
        "exploration:explore",
        {"exploration_result": "success"},
    )
    return {"exploration_result": "success"}


@celery_app.task
def integrate_maps(correlation_id, saga_id, fail=False):
    logger.info(f"Saga[{saga_id}]: Integrating maps (correlation_id={correlation_id})")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Map integration failed!")
        emit_event(
            "mission:events",
            correlation_id,
            saga_id,
            "map:failed",
            "failed",
            {"error": "Map integration failed"},
        )
        raise Exception("Map integration failed")
    logger.info(f"Saga[{saga_id}]: Maps integrated")
    emit_command(
        "map:commands",
        correlation_id,
        saga_id,
        "map:integrate",
        {"final_map": "integrated_map"},
    )
    return {"final_map": "integrated_map"}


# Compensation tasks


@celery_app.task
def release_resources(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Releasing allocated robots (correlation_id={correlation_id})")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Robots released")
    return {"released": True, "correlation_id": correlation_id}


@celery_app.task
def abort_exploration(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Aborting exploration (correlation_id={correlation_id})")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Exploration aborted")
    return {"aborted": True, "correlation_id": correlation_id}


@celery_app.task
def rollback_integration(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Rolling back map integration (correlation_id={correlation_id})")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Map integration rolled back")
    return {"rolled_back": True, "correlation_id": correlation_id}
