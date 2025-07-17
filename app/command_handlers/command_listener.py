import importlib
import pkgutil
import asyncio

def discovery_handler_modules():
    """
    Discover handler modules under app.command_handlers.handlers.

    Returns:
        List of dicts with keys: name, stream, group, handle
    """
    handlers = []
    package = importlib.import_module("app.command_handlers.handlers")
    for name, ispkg in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"app.command_handlers.handlers.{name}")
        handlers.append({
            "name": name,
            "stream": getattr(module, "STREAM_NAME", None),
            "group": getattr(module, "GROUP_NAME", None),
            "handle": getattr(module, "handle", None),
        })
    return handlers

async def run_command_listeners(redis_client):
    """
    Asynchronously listen to each handler's stream and process messages.
    Assumes aioredis backend and async handler functions.
    """
    handlers = discovery_handler_modules()
    async def listen_handler(handler):
        stream = handler["stream"]
        group = handler["group"]
        handle_fn = handler["handle"]
        if not (stream and group and handle_fn):
            return
        while True:
            try:
                # Replace with actual aioredis XREADGROUP call
                messages = await redis_client.xread_group(group, "listener", streams={stream: ">"}, count=10, latest_ids=None, timeout=1000)
                for msg_id, fields in messages.get(stream, []):
                    await handle_fn(fields)
                    await redis_client.xack(stream, group, msg_id)
            except Exception as e:
                print(f"Error in handler {handler['name']}: {e}")
            await asyncio.sleep(0.1)

    await asyncio.gather(*(listen_handler(h) for h in handlers))
