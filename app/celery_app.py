import os
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("saga_app", broker=broker_url, backend=backend_url)
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)

celery_app.autodiscover_tasks(['app'])
