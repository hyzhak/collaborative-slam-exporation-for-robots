import importlib
import pkgutil
import asyncio
import logging

logger = logging.getLogger(__name__)

def discovery_handler_modules():
    """
    Discover handler modules under app.command_handlers.handlers.

    Returns:
        List of dicts with keys: name, stream, group, event_type, handle
    """
    handlers = []
    package = importlib.import_module("app.command_handlers.handlers")
    for name, ispkg in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"app.command_handlers.handlers.{name}")
        handlers.append({
            "name": name,
            "stream": getattr(module, "STREAM_NAME", None),
            "group": getattr(module, "GROUP_NAME", None),
            "event_type": getattr(module, "EVENT_TYPE", None),
            "handle": getattr(module, "handle", None),
        })
    logger.debug("Discovered %d handler modules", len(handlers))
    return handlers

async def run_command_listeners(redis_client):
    """
    Asynchronously listen to each handler's stream and process messages.
    Assumes aioredis backend and async handler functions.
    """
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

        logger.info("Handler %s listening on stream '%s', group '%s'", name, stream, group)
        while True:
            try:
                logger.debug("xread_group: group=%s, consumer=listener, stream=%s", group, stream)
                messages = await redis_client.xread_group(
                    group,
                    "listener",
                    streams={stream: ">"},
                    count=10,
                    latest_ids=None,
                    timeout=1000,
                )
                for msg_id, fields in messages.get(stream, []):
                    msg_event = fields.get("event_type")
                    if event_type and msg_event != event_type:
                        logger.debug(
                            "Skipping message %s on stream %s: event_type '%s' != '%s'",
                            msg_id, stream, msg_event, event_type
                        )
                        continue
                    logger.info("Invoking handler %s for message %s", name, msg_id)
                    try:
                        await handle_fn(fields)
                        await redis_client.xack(stream, group, msg_id)
                        logger.info("Acked message %s on stream %s", msg_id, stream)
                    except Exception as e:
                        logger.error(
                            "Handler %s failed for message %s", name, msg_id, exc_info=e
                        )
            except Exception as e:
                logger.error(
                    "Listener error in handler %s for stream %s", name, stream, exc_info=e
                )
            await asyncio.sleep(0.1)

    await asyncio.gather(*(listen_handler(h) for h in handlers))
