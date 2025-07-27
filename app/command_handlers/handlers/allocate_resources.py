import asyncio
from app.redis_utils.decorators import multi_stage_reply
import logging


STREAM_NAME = "resources:commands"
GROUP_NAME = "resources_handler_group"
EVENT_TYPE = "resources:allocate"

logger = logging.getLogger(__name__)


@multi_stage_reply
async def handle(fields: dict, progress) -> None:
    """
    Handle allocate_resources command.
    """
    logger.info("Handling allocate_resources command")
    await progress(0.5, {"stage": "allocating"})
    await asyncio.sleep(1)
