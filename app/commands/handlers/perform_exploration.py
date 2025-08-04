import asyncio
import logging
from app.redis_utils.decorators import multi_stage_reply

STREAM_NAME = "exploration:commands"
GROUP_NAME = "exploration_handler_group"
EVENT_TYPE = "exploration:perform"

logger = logging.getLogger(__name__)

@multi_stage_reply
async def handle(fields: dict, progress) -> None:
    """
    Handle perform_exploration command.
    """
    logger.info("Handling perform_exploration command")
    await progress(0.5, {"stage": "exploring"})
    await asyncio.sleep(1)
