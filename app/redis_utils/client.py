import os
import redis.asyncio as redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
