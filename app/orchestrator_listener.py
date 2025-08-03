import os
import time
import logging
import redis
from app.orchestrator import run_saga
from app.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_STREAM = os.environ.get("REDIS_STREAM", "mission:commands")
GROUP_NAME = "orchestrator_group"
CONSUMER_NAME = "orchestrator_1"


def ensure_group(r):
    try:
        r.xgroup_create(REDIS_STREAM, GROUP_NAME, id="0", mkstream=True)
        logger.info(f"Created group {GROUP_NAME} on stream {REDIS_STREAM}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"Group {GROUP_NAME} already exists")
        else:
            raise


def main():
    # Wait for Redis to be available
    for _ in range(30):
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            r.ping()
            break
        except Exception:
            logger.info("Waiting for Redis to be available...")
            time.sleep(1)
    else:
        logger.error("Redis not available after 30 seconds, exiting.")
        return

    ensure_group(r)
    logger.info(f"Listening for new saga requests on stream '{REDIS_STREAM}'...")
    while True:
        try:
            resp = r.xreadgroup(
                GROUP_NAME, CONSUMER_NAME, {REDIS_STREAM: ">"}, count=1, block=5000
            )
            if resp:
                for stream, messages in resp:
                    for msg_id, fields in messages:
                        robot_count = int(fields.get("robot_count", 2))
                        area = fields.get("area", "ZoneB")
                        correlation_id = fields.get("correlation_id")
                        if not correlation_id:
                            logger.error("Missing correlation_id in incoming command, skipping message.")
                            r.xack(REDIS_STREAM, GROUP_NAME, msg_id)
                            continue
                        logger.info(
                            f"Received saga request: robot_count={robot_count}, area={area}, correlation_id={correlation_id}"
                        )
                        try:
                            run_saga(robot_count, area, correlation_id=correlation_id)
                            r.xack(REDIS_STREAM, GROUP_NAME, msg_id)
                        except Exception as e:
                            logger.error(f"Failed to process saga request: {e}")
        except Exception as e:
            logger.error(f"Listener error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
