import functools
import inspect
from .commands import emit_event

def multi_stage_reply(func):
    """
    Decorator for command handlers to emit start, progress, completed, and failed events.
    Injects a 'progress' callback if the handler accepts it.
    The 'completed' payload will include the handler's return value (if not None).
    """
    @functools.wraps(func)
    def wrapper(fields, *args, **kwargs):
        stream = fields.get("stream")
        correlation_id = fields.get("correlation_id")
        saga_id = fields.get("saga_id")
        event_type = fields.get("event_type")

        def progress(fraction: float, payload: dict = None):
            emit_event(
                stream,
                correlation_id,
                saga_id,
                event_type,
                status="progress",
                payload={"fraction": fraction, **(payload or {})},
            )

        # Emit start event
        emit_event(
            stream,
            correlation_id,
            saga_id,
            event_type,
            status="start",
            payload={},
        )

        try:
            sig = inspect.signature(func)
            if "progress" in sig.parameters:
                result = func(fields, progress=progress, *args, **kwargs)
            else:
                result = func(fields, *args, **kwargs)
            # Emit completed event with result as payload if not None
            completed_payload = {}
            if result is not None:
                if isinstance(result, dict):
                    completed_payload = result
                else:
                    completed_payload = {"result": result}
            emit_event(
                stream,
                correlation_id,
                saga_id,
                event_type,
                status="completed",
                payload=completed_payload,
            )
            return result
        except Exception as e:
            # Emit failed event
            emit_event(
                stream,
                correlation_id,
                saga_id,
                event_type,
                status="failed",
                payload={"error": str(e)},
            )
            raise

    return wrapper
