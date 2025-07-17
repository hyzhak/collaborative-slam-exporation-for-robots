STREAM_NAME = "resources:commands"
GROUP_NAME = "resources_handler_group"
EVENT_TYPE = "resources:release"


def handle(fields: dict):
    """
    Handle a release resources command.

    Args:
        fields (dict): Command fields from Redis Stream.

    Returns:
        dict: Result of release operation.

    Raises:
        NotImplementedError: If not implemented.
    """
    raise NotImplementedError("ReleaseResourcesHandler.handle must be implemented.")
