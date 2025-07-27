import json
import logging
import time
from .client import get_redis_client
from opentelemetry import trace

logger = logging.getLogger(__name__)

async def emit_command(
    stream,
    correlation_id,
    saga_id,
    event_type,
    payload,
    request_id=None,
    traceparent=None,
    maxlen=None,
    ttl=None,
    reply_stream=None,
):
    logger.info(
        f"Emitting command: {stream}, correlation_id={correlation_id}, saga_id={saga_id}, event_type={event_type}, request_id={request_id}"
    )
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    if request_id is not None:
        fields["request_id"] = request_id
    if traceparent is not None:
        fields["traceparent"] = traceparent
    if reply_stream is not None:
        fields["reply_stream"] = reply_stream
    xadd_kwargs = {}
    if maxlen is not None:
        xadd_kwargs["maxlen"] = maxlen
        xadd_kwargs["approximate"] = True

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("emit_command") as span:
        span.set_attribute("stream", stream)
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("saga_id", saga_id)
        span.set_attribute("event_type", event_type)
        if request_id is not None:
            span.set_attribute("request_id", request_id)
        if traceparent is not None:
            span.set_attribute("traceparent", traceparent)
        entry_id = await r.xadd(stream, fields, **xadd_kwargs)
        if ttl is not None:
            await r.expire(stream, ttl)
        span.set_attribute("entry_id", entry_id)
        return entry_id

async def emit_event(
    stream, correlation_id, saga_id, event_type, status, payload, maxlen=None, ttl=None
):
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "status": status,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    xadd_kwargs = {}
    if maxlen is not None:
        xadd_kwargs["maxlen"] = maxlen
        xadd_kwargs["approximate"] = True
    entry_id = await r.xadd(stream, fields, **xadd_kwargs)
    if ttl is not None:
        await r.expire(stream, ttl)
    return entry_id
