from app.logging_config import setup_logging
setup_logging()

import logging
import random
import time
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def allocate_resources(saga_id, robot_count, fail=False):
    logger.info(f"Saga[{saga_id}]: Allocating {robot_count} robots")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Allocation failed!")
        raise Exception("Allocation failed")
    logger.info(f"Saga[{saga_id}]: Successfully allocated robots")
    return {"robots_allocated": robot_count}


@celery_app.task
def plan_route(saga_id, area, fail=False):
    logger.info(f"Saga[{saga_id}]: Planning route for area {area}")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Route planning failed!")
        raise Exception("Route planning failed")
    logger.info(f"Saga[{saga_id}]: Route planned")
    return {"route": f"Route for {area}"}


@celery_app.task
def perform_exploration(saga_id, robot_count, fail=False):
    logger.info(f"Saga[{saga_id}]: Performing exploration with {robot_count} robots")
    time.sleep(2)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Exploration failed!")
        raise Exception("Exploration failed")
    logger.info(f"Saga[{saga_id}]: Exploration complete")
    return {"exploration_result": "success"}


@celery_app.task
def integrate_maps(saga_id, fail=False):
    logger.info(f"Saga[{saga_id}]: Integrating maps")
    time.sleep(0.5)
    if fail or random.random() < 0.1:
        logger.error(f"Saga[{saga_id}]: Map integration failed!")
        raise Exception("Map integration failed")
    logger.info(f"Saga[{saga_id}]: Maps integrated")
    return {"final_map": "integrated_map"}


# Compensation tasks


@celery_app.task
def release_resources(saga_id):
    logger.info(f"Saga[{saga_id}]: Releasing allocated robots")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Robots released")
    return {"released": True}


@celery_app.task
def abort_exploration(saga_id):
    logger.info(f"Saga[{saga_id}]: Aborting exploration")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Exploration aborted")
    return {"aborted": True}


@celery_app.task
def rollback_integration(saga_id):
    logger.info(f"Saga[{saga_id}]: Rolling back map integration")
    time.sleep(0.25)
    logger.info(f"Saga[{saga_id}]: Map integration rolled back")
    return {"rolled_back": True}
