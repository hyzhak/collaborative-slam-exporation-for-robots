import logging
import time

STREAM_NAME = "exploration:commands"
GROUP_NAME = "exploration_handler_group"
EVENT_TYPE = "exploration:perform"

logger = logging.getLogger(__name__)

from app.redis_utils.decorators import multi_stage_reply

@multi_stage_reply
def handle(fields: dict, progress) -> None:
    """
    Handle perform_exploration command.
    """
    logger.info("Handling perform_exploration command")
    progress(0.5, {"stage": "exploring"})
    time.sleep(1)
