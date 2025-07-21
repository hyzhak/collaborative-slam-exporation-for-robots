import logging
import time

STREAM_NAME = "routing:commands"
GROUP_NAME = "routing_handler_group"
EVENT_TYPE = "routing:plan"

logger = logging.getLogger(__name__)

from app.redis_utils.decorators import multi_stage_reply

@multi_stage_reply
def handle(fields: dict, progress) -> None:
    """
    Handle plan_route command.
    """
    logger.info("Handling plan_route command")
    progress(0.5, {"stage": "planning"})
    time.sleep(1)
