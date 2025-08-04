import asyncio
import logging

from app.redis_utils.decorators import multi_stage_reply

STREAM_NAME = "routing:commands"
GROUP_NAME = "routing_handler_group"
EVENT_TYPE = "routing:plan"

logger = logging.getLogger(__name__)

@multi_stage_reply
async def handle(fields: dict, progress) -> None:
    """
    Handle plan_route command.
    """
    logger.info("Handling plan_route command")
    await progress(0.5, {"stage": "planning"})
    await asyncio.sleep(1)
