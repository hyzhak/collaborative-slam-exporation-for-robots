import asyncio
import logging

from app.redis_utils.decorators import multi_stage_reply


STREAM_NAME = "resources:commands"
GROUP_NAME = "resources_release_group"
EVENT_TYPE = "resources:release"

logger = logging.getLogger(__name__)


@multi_stage_reply
async def handle(fields: dict, progress) -> None:
    """
    Handle release_resources command.
    """
    logger.info(f"Handling release_resources command {fields}")
    await progress(0.5, {"stage": "releasing"})
    await asyncio.sleep(1)
