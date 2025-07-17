import logging
import time

STREAM_NAME = "map:commands"
GROUP_NAME = "map_handler_group"
EVENT_TYPE = "map:integrate"

logger = logging.getLogger(__name__)

def handle(fields: dict) -> None:
    """
    Handle integrate_maps command.
    """
    logger.info("Handling integrate_maps command")
    time.sleep(1)
