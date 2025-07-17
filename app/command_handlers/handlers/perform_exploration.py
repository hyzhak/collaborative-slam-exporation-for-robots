import logging
import time

STREAM_NAME = "exploration:commands"
GROUP_NAME = "exploration_handler_group"
EVENT_TYPE = "exploration:perform"

logger = logging.getLogger(__name__)

def handle(fields: dict) -> None:
    """
    Handle perform_exploration command.
    """
    logger.info("Handling perform_exploration command")
    time.sleep(1)
