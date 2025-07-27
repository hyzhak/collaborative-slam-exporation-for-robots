import importlib
import pkgutil
import asyncio
import logging

from app.logging_config import setup_logging
from app.redis_utils.client import get_redis_client

setup_logging()

logger = logging.getLogger(__name__)

def discovery_handler_modules():
    """
    Discover handler modules under app.command_handlers.handlers.

    Returns:
        List of dicts with keys: name, stream, group, event_type, handle
    """
    handlers = []
    package = importlib.import_module("app.command_handlers.handlers")
    logger.info(f"Discovering command handler modules in {package.__name__}")
    for module_info in list(pkgutil.iter_modules(package.__path__)):
        name = module_info.name
        ispkg = module_info.ispkg
        logger.debug(f"Found module: {name}, is package: {ispkg}")
        try:
            module = importlib.import_module(f"app.command_handlers.handlers.{name}")
            logger.debug(f"Loaded handler module: {name}")
        except ModuleNotFoundError:
            logger.warning(f"Handler module {name} not found, skipping")
            continue
        logger.debug(f"Discovered handler module: {name}")
        handlers.append({
            "name": name,
            "stream": getattr(module, "STREAM_NAME", None),
            "group": getattr(module, "GROUP_NAME", None),
            "event_type": getattr(module, "EVENT_TYPE", None),
            "handle": getattr(module, "handle", None),
        })
    logger.debug(f"Discovered {len(handlers)} handler modules")
    return handlers

async def run_command_listeners(redis_client=None):
    """
    Asynchronously listen to each handler's stream and process messages.
    Assumes aioredis backend and async handler functions.
    Accepts optional redis_client for testing.
    """
    logger.info("Starting command listeners")
    if redis_client is None:
        redis_client = get_redis_client()
    handlers = discovery_handler_modules()
    logger.info("Starting command listeners with %d handlers", len(handlers))

    async def listen_handler(handler):
        name = handler["name"]
        stream = handler["stream"]
        group = handler["group"]
        event_type = handler.get("event_type")
        handle_fn = handler["handle"]
        if not (stream and group and handle_fn):
            logger.warning("Skipping handler %s due to incomplete metadata", name)
            return

        # Ensure consumer group exists before entering read loop
        try:
            await redis_client.xgroup_create(
                name=stream,
                groupname=group,
                id="$",
                mkstream=True
            )
            logger.info(f"Created consumer group '{group}' for stream '{stream}'")
        except Exception as e:
            # BUSYGROUP means group already exists
            if hasattr(e, "args") and e.args and "BUSYGROUP" in str(e.args[0]):
                logger.info(f"Consumer group '{group}' for stream '{stream}' already exists")
            else:
                logger.error(f"Failed to create consumer group '{group}' for stream '{stream}'", exc_info=e)
                raise

        logger.info(f"Handler {name} listening on stream '{stream}', group '{group}'")
        while True:
            try:
                logger.debug(f"xreadgroup: group={group}, consumer=listener, stream={stream}")
                entries = await redis_client.xreadgroup(
                    groupname=group,
                    consumername="listener",
                    block=1000,
                    count=10,
                    streams={stream: ">"}
                )
                for stream_name, msgs in entries:
                    for msg_id, fields in msgs:
                        msg_event = fields.get("event_type")
                        if event_type and msg_event != event_type:
                            logger.debug(f"Skipping message {msg_id} on stream {stream}: event_type '{msg_event}' != '{event_type}'")
                            continue
                        logger.info(f"Invoking handler {name} for message {msg_id}")
                        try:
                            await handle_fn(fields)
                            await redis_client.xack(stream, group, msg_id)
                            logger.info(f"Acked message {msg_id} on stream {stream}")
                        except Exception as e:
                            logger.error(
                                f"Handler {name} failed for message {msg_id}", exc_info=e
                            )
            except Exception as e:
                logger.error(
                    f"Listener error in handler {name} for stream {stream}", exc_info=e
                )
            await asyncio.sleep(0.1)

    await asyncio.gather(*(listen_handler(h) for h in handlers))

if __name__ == "__main__":
    logger.info("Starting Async Command Listeners")
    asyncio.run(run_command_listeners())
