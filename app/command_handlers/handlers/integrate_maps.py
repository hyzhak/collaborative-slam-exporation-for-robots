import logging
import time
from app.redis_utils.decorators import multi_stage_reply

STREAM_NAME = "map:commands"
GROUP_NAME = "map_handler_group"
EVENT_TYPE = "map:integrate"

logger = logging.getLogger(__name__)

@multi_stage_reply
def handle(fields: dict, progress) -> None:
    """
    Handle integrate_maps command.
    """
    logger.info("Handling integrate_maps command")
    progress(0.5, {"stage": "integrating"})
    time.sleep(1)
