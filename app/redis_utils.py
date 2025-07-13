import os
import redis
import json
import time

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))


def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def emit_command(stream, correlation_id, saga_id, event_type, payload):
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    return r.xadd(stream, fields)


def emit_event(stream, correlation_id, saga_id, event_type, status, payload):
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "status": status,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    return r.xadd(stream, fields)
