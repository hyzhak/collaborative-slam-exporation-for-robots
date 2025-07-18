from app.logging_config import setup_logging
setup_logging()

import logging
from .celery_app import celery_app
from .redis_utils import emit_command, emit_event

logger = logging.getLogger(__name__)


@celery_app.task
def allocate_resources(correlation_id, saga_id, robot_count):
    logger.info(f"Saga[{saga_id}]: Allocating {robot_count} robots (correlation_id={correlation_id})")
    emit_command(
        "resources:commands",
        correlation_id,
        saga_id,
        "resources:allocate",
        {"robots_allocated": robot_count},
    )
    return {"robots_allocated": robot_count}


@celery_app.task
def plan_route(correlation_id, saga_id, area):
    logger.info(f"Saga[{saga_id}]: Planning route for area {area} (correlation_id={correlation_id})")
    emit_command(
        "routing:commands",
        correlation_id,
        saga_id,
        "routing:plan",
        {"route": f"Route for {area}"},
    )
    return {"route": f"Route for {area}"}


@celery_app.task
def perform_exploration(correlation_id, saga_id, robot_count):
    logger.info(f"Saga[{saga_id}]: Performing exploration with {robot_count} robots (correlation_id={correlation_id})")
    emit_command(
        "exploration:commands",
        correlation_id,
        saga_id,
        "exploration:perform",
        {"exploration_result": "success"},
    )
    return {"exploration_result": "success"}


@celery_app.task
def integrate_maps(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Integrating maps (correlation_id={correlation_id})")
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
    return {"released": True, "correlation_id": correlation_id}


@celery_app.task
def abort_exploration(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Aborting exploration (correlation_id={correlation_id})")
    return {"aborted": True, "correlation_id": correlation_id}


@celery_app.task
def rollback_integration(correlation_id, saga_id):
    logger.info(f"Saga[{saga_id}]: Rolling back map integration (correlation_id={correlation_id})")
    return {"rolled_back": True, "correlation_id": correlation_id}
