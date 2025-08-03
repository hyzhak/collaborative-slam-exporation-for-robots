from app.logging_config import setup_logging
import asyncio
import logging
from opentelemetry import trace
import time
import uuid

from .client import get_redis_client
from .commands import emit_command
from .retries import exponential_retry

setup_logging()

logger = logging.getLogger(__name__)


async def read_replies(
    stream, correlation_id, request_id, timeout, retry_strategy=None, traceparent=None
):
    """
    Blocking read for reply stream using XREADGROUP. 
    Returns only the 'completed' reply message as a dict.
    Logs 'start' and 'progress' messages.
    Raises TimeoutError if no 'completed' reply within timeout.
    retry_strategy: a callable (attempt, elapsed, last_delay) -> delay (seconds) or None for immediate fail.
    Supports exponential, linear, or custom retry logic.
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("read_replies") as span:
        span.set_attribute("stream", stream)
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("request_id", request_id)
        span.set_attribute("timeout", timeout)
        if traceparent is not None:
            span.set_attribute("traceparent", traceparent)

        r = get_redis_client()
        group_name = f"{stream}.{request_id}.group"
        consumer_name = f"read_replies-{request_id}"
        attempt = 0
        elapsed = 0
        last_delay = 0
        start_time = time.time()

        # Ensure consumer group exists
        try:
            await r.xgroup_create(stream, group_name, id="0", mkstream=True)
        except Exception as e:
            logger.warning(f"Error creating consumer group: {e}")
            if "BUSYGROUP" not in str(e):
                raise

        last_id = ">"
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            remaining = timeout - elapsed
            # logger.debug(
            #     f"[read_replies] attempt={attempt}, elapsed={elapsed:.3f}, last_delay={last_delay}, last_id={last_id}"
            # )
            block_ms = int(remaining * 1000)
            resp = await r.xreadgroup(
                group_name,
                consumer_name,
                {stream: last_id},
                count=1,
                block=block_ms,
            )
            # logger.debug(f"[read_replies] xreadgroup resp={resp}")
            if resp:
                _, entries = resp[0]
                logger.debug(f"[read_replies] entries={entries}")
                for entry in entries:
                    logger.debug(f"[read_replies] entry={entry}")
                    if isinstance(entry, tuple) and len(entry) == 2:
                        entry_id, fields = entry
                    elif isinstance(entry, dict):
                        entry_id, fields = next(iter(entry.items()))
                    else:
                        logger.warning(
                            f"[read_replies] unexpected entry format: {entry}"
                        )
                        continue
                    last_id = entry_id
                    # Acknowledge the message in the consumer group
                    try:
                        await r.xack(stream, group_name, entry_id)
                        logger.debug(f"[read_replies] acknowledged entry_id={entry_id}")
                    except Exception as ack_err:
                        logger.warning(f"[read_replies] failed to acknowledge entry_id={entry_id}: {ack_err}")
                    status = fields.get("status")
                    logger.debug(
                        f"[read_replies] entry_id={entry_id}, status={status}, fields={fields}"
                    )
                    if status == "completed":
                        logger.info(f"[read_replies] completed reply: {fields}")
                        span.set_attribute("reply_entry_id", entry_id)
                        span.set_attribute("reply_status", status)
                        return fields
                    elif status in ("start", "progress"):
                        logger.info(
                            f"[read_replies] Reply status: {status}, fields: {fields}"
                        )
            else:
                attempt += 1
                elapsed = time.time() - start_time
                logger.debug(
                    f"[read_replies] no entries, attempt={attempt}, elapsed={elapsed:.3f}"
                )
                if retry_strategy:
                    delay = retry_strategy(attempt, elapsed, last_delay)
                    logger.debug(
                        f"[read_replies] retry_strategy returned delay={delay}"
                    )
                    if delay is None or elapsed + delay > timeout:
                        logger.warning(
                            f"[read_replies] breaking retry loop: delay={delay}, elapsed={elapsed}, timeout={timeout}"
                        )
                        break
                    await asyncio.sleep(delay)
                    last_delay = delay
                else:
                    logger.warning("[read_replies] no retry_strategy, breaking loop")
                    break
        logger.error(
            f"[read_replies] TimeoutError: No 'completed' reply received in {timeout} seconds for correlation_id={correlation_id}, request_id={request_id}"
        )
        span.set_attribute("timeout", True)
        raise TimeoutError(
            f"No 'completed' reply received in {timeout} seconds for correlation_id={correlation_id}, request_id={request_id}"
        )


async def request_and_reply(
    command_stream,
    response_prefix,
    correlation_id,
    saga_id,
    event_type,
    payload,
    timeout=30,
):
    """
    Internal helper to emit a command and block for the completed reply.
    """

    request_id = uuid.uuid4().hex
    traceparent = request_id
    reply_stream = f"{response_prefix}:{request_id}"
    
    logger.info(
        f"Requesting command: {command_stream}, correlation_id={correlation_id}, saga_id={saga_id}, event_type={event_type}, request_id={request_id}"
    )
    await emit_command(
        command_stream,
        correlation_id,
        saga_id,
        event_type,
        payload,
        reply_stream=reply_stream,
        request_id=request_id,
        traceparent=traceparent,
    )
    logger.info(
        f"Waiting for reply: {reply_stream}, request_id={request_id}, traceparent={traceparent}"
    )
    try:
        return await read_replies(
            reply_stream,
            correlation_id,
            request_id,
            timeout=timeout,
            traceparent=traceparent,
            retry_strategy=exponential_retry(),
        )
    except TimeoutError as e:
        logger.warning(f"No reply for command {command_stream}, proceeding without response: {e}")
        return {}
