import logging
import os

from app.redis_utils.decorators import multi_stage_reply
from app.redis_utils.replies import request_and_reply


STREAM_NAME = os.environ.get("REDIS_STREAM", "mission:commands")
GROUP_NAME = "mission_orchestrator_group"
EVENT_TYPE = "mission:start"

logger = logging.getLogger(__name__)

@multi_stage_reply
async def handle(fields):
    """
    Trigger the full saga flow in response to a mission:start event.
    """
    
    logger.info(f"Handling orchestrator trigger command {fields}")

    from app.orchestrator import run_saga

    correlation_id = fields.get("correlation_id")
    if not correlation_id:
        raise ValueError("Missing correlation_id in fields")

    # Extract parameters
    robot_count = int(fields.get("robot_count", 2))
    area = fields.get("area")

    # Dispatch saga via Celery canvas
    result = await run_saga(robot_count, area, correlation_id=correlation_id)
    return result.id
    # return await request_and_reply(
    #     "resources:commands",
    #     "resources:replies",
    #     'correlation_id',
    #     'saga_id',
    #     "resources:allocate",
    #     {"robots_allocated": robot_count},
    # )
