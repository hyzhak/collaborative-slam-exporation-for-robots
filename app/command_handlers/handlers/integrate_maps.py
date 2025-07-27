import logging
import asyncio
from app.redis_utils.decorators import multi_stage_reply

STREAM_NAME = "map:commands"
GROUP_NAME = "map_handler_group"
EVENT_TYPE = "map:integrate"

logger = logging.getLogger(__name__)

@multi_stage_reply
async def handle(fields: dict, progress) -> None:
    """
    Handle integrate_maps command.
    """
    logger.info("Handling integrate_maps command")
    await progress(0.5, {"stage": "integrating"})
    await asyncio.sleep(1)
