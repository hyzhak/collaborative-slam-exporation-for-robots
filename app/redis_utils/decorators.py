import functools
import inspect
from .commands import emit_event

def multi_stage_reply(func):
    """
    Decorator for command handlers to emit start, progress, completed, and failed events.
    Injects a 'progress' callback if the handler accepts it.
    The 'completed' payload will include the handler's return value (if not None).
    Emits to reply_stream if present in fields, otherwise uses stream.
    """
    @functools.wraps(func)
    async def wrapper(fields, *args, **kwargs):
        reply_stream = fields.get("reply_stream")
        correlation_id = fields.get("correlation_id")
        saga_id = fields.get("saga_id")
        event_type = fields.get("event_type")

        emit_args = [
            reply_stream,
            correlation_id,
            saga_id,
            event_type,
        ]

        async def progress(fraction: float, payload: dict = None):
            await emit_event(
                *emit_args,
                status="progress",
                payload={"fraction": fraction, **(payload or {})},
            )

        # Emit start event
        await emit_event(
            *emit_args,
            status="start",
            payload={},
        )

        try:
            sig = inspect.signature(func)
            if "progress" in sig.parameters:
                result = await func(fields, progress=progress, *args, **kwargs)
            else:
                result = await func(fields, *args, **kwargs)
            # Emit completed event with result as payload if not None
            completed_payload = {}
            if result is not None:
                if isinstance(result, dict):
                    completed_payload = result
                else:
                    completed_payload = {"result": result}
            await emit_event(
                *emit_args,
                status="completed",
                payload=completed_payload,
            )
            return result
        except Exception as e:
            # Emit failed event
            await emit_event(
                *emit_args,
                status="failed",
                payload={"error": str(e)},
            )
            raise

    return wrapper
