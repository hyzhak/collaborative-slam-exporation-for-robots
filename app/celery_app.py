import os
import redis
import time
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Wait for Redis to be available before starting Celery

redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
for _ in range(30):
    try:
        r = redis.Redis(host=redis_host, port=redis_port)
        r.ping()
        break
    except Exception:
        print("Waiting for Redis to be available for Celery...")
        time.sleep(1)
else:
    raise RuntimeError("Redis not available after 30 seconds for Celery.")

celery_app = Celery("saga_app", broker=broker_url, backend=backend_url)
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)
celery_app.autodiscover_tasks(["app"])
