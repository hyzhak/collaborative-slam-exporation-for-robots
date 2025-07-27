import os
STREAM_NAME = os.environ.get("REDIS_STREAM", "mission:commands")
GROUP_NAME = "orchestrator_group"
EVENT_TYPE = "mission:start"

async def handle(fields):
    """
    Trigger the full saga flow in response to a mission:start event.
    """
    from app.orchestrator import run_saga

    correlation_id = fields.get("correlation_id")
    if not correlation_id:
        # Missing correlation_id, nothing to do
        return

    # Extract parameters
    robot_count = int(fields.get("robot_count", 2))
    area = fields.get("area", "ZoneA")

    # Dispatch saga via Celery canvas
    run_saga(robot_count, area, correlation_id=correlation_id)
