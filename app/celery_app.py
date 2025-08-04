from app.logging_config import setup_logging
from celery import Celery
import logging
import os
import redis
import time

setup_logging()


logger = logging.getLogger(__name__)

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
logger.info(f"Using broker URL: {broker_url}")
backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
logger.info(f"Using backend URL: {backend_url}")

# Wait for Redis to be available before starting Celery

redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
for _ in range(30):
    try:
        r = redis.Redis(host=redis_host, port=redis_port)
        r.ping()
        break
    except Exception:
        logger.debug("Waiting for Redis to be available for Celery...")
        time.sleep(1)
else:
    raise RuntimeError("Redis not available after 30 seconds for Celery.")

celery_app = Celery("saga_app", broker=broker_url, backend=backend_url)
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)
logger.info("Celery app configured with broker and backend")
celery_app.autodiscover_tasks(["app.flows.mission_start_celery.tasks"])
logger.info("Celery tasks autodiscovered")
