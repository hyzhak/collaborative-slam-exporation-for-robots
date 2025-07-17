STREAM_NAME = "exploration:commands"
GROUP_NAME = "exploration_handler_group"
EVENT_TYPE = "exploration:perform"


def handle(fields: dict) -> None:
    """
    Handle perform_exploration command.
    """
    raise NotImplementedError("Handler not implemented yet")
