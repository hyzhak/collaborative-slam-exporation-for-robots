import logging
import time

STREAM_NAME = "routing:commands"
GROUP_NAME = "routing_handler_group"
EVENT_TYPE = "routing:plan"

logger = logging.getLogger(__name__)

def handle(fields: dict) -> None:
    """
    Handle plan_route command.
    """
    logger.info("Handling plan_route command")
    time.sleep(1)
