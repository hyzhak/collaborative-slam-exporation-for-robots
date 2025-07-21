import json
import time
from .client import get_redis_client

def emit_command(
    stream,
    correlation_id,
    saga_id,
    event_type,
    payload,
    request_id=None,
    traceparent=None,
    maxlen=None,
    ttl=None,
):
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
    xadd_kwargs = {}
    if maxlen is not None:
        xadd_kwargs["maxlen"] = maxlen
        xadd_kwargs["approximate"] = True
    entry_id = r.xadd(stream, fields, **xadd_kwargs)
    if ttl is not None:
        r.expire(stream, ttl)
    return entry_id

def emit_event(
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
    entry_id = r.xadd(stream, fields, **xadd_kwargs)
    if ttl is not None:
        r.expire(stream, ttl)
    return entry_id
