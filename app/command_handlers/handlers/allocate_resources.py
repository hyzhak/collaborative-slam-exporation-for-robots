import logging
import time

STREAM_NAME = "resources:commands"
GROUP_NAME = "resources_handler_group"
EVENT_TYPE = "resources:allocate"

logger = logging.getLogger(__name__)


def handle(fields: dict) -> None:
    """
    Handle allocate_resources command.
    """
    logger.info("Handling allocate_resources command")
    time.sleep(1)
