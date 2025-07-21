import logging
import time

STREAM_NAME = "resources:commands"
GROUP_NAME = "resources_handler_group"
EVENT_TYPE = "resources:release"

logger = logging.getLogger(__name__)

from app.redis_utils.decorators import multi_stage_reply

@multi_stage_reply
def handle(fields: dict, progress) -> None:
    """
    Handle release_resources command.
    """
    logger.info("Handling release_resources command")
    progress(0.5, {"stage": "releasing"})
    time.sleep(1)
