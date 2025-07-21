import logging
import time
import uuid

from opentelemetry import trace

from .client import get_redis_client
from .retries import exponential_retry

def read_replies(
    stream, correlation_id, request_id, timeout, retry_strategy=None, traceparent=None
):
    """
    Blocking read for reply stream using XREADGROUP.
    Returns only the 'completed' reply message as a dict.
    Logs 'start' and 'progress' messages.
    Raises TimeoutError if no 'completed' message within timeout.
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
        group_name = f"{stream}:group"
        consumer_name = f"reader-{uuid.uuid4().hex}"
        start_id = ">"
        attempt = 0
        elapsed = 0
        last_delay = 0
        start_time = time.time()

        # Ensure consumer group exists
        try:
            r.xgroup_create(stream, group_name, id="0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

        last_id = "0"
        while elapsed < timeout:
            logging.debug(
                f"[read_replies] attempt={attempt}, elapsed={elapsed:.3f}, last_delay={last_delay}, last_id={last_id}"
            )
            resp = r.xreadgroup(
                group_name,
                consumer_name,
                {stream: last_id},
                count=1,
                block=int(last_delay * 1000) if last_delay else 0,
            )
            logging.debug(f"[read_replies] xreadgroup resp={resp}")
            if resp:
                _, entries = resp[0]
                logging.debug(f"[read_replies] entries={entries}")
                for entry in entries:
                    logging.debug(f"[read_replies] entry={entry}")
                    if isinstance(entry, tuple) and len(entry) == 2:
                        entry_id, fields = entry
                    elif isinstance(entry, dict):
                        entry_id, fields = next(iter(entry.items()))
                    else:
                        logging.warning(f"[read_replies] unexpected entry format: {entry}")
                        continue
                    last_id = entry_id
                    status = fields.get("status")
                    logging.debug(
                        f"[read_replies] entry_id={entry_id}, status={status}, fields={fields}"
                    )
                    if status == "completed":
                        logging.info(f"[read_replies] completed reply: {fields}")
                        span.set_attribute("reply_entry_id", entry_id)
                        span.set_attribute("reply_status", status)
                        return fields
                    elif status in ("start", "progress"):
                        logging.info(
                            f"[read_replies] Reply status: {status}, fields: {fields}"
                        )
            else:
                attempt += 1
                elapsed = time.time() - start_time
                logging.debug(
                    f"[read_replies] no entries, attempt={attempt}, elapsed={elapsed:.3f}"
                )
                if retry_strategy:
                    delay = retry_strategy(attempt, elapsed, last_delay)
                    logging.debug(f"[read_replies] retry_strategy returned delay={delay}")
                    if delay is None or elapsed + delay > timeout:
                        logging.warning(
                            f"[read_replies] breaking retry loop: delay={delay}, elapsed={elapsed}, timeout={timeout}"
                        )
                        break
                    time.sleep(delay)
                    last_delay = delay
                else:
                    logging.warning("[read_replies] no retry_strategy, breaking loop")
                    break
        logging.error(
            f"[read_replies] TimeoutError: No 'completed' reply received in {timeout} seconds for correlation_id={correlation_id}, request_id={request_id}"
        )
        span.set_attribute("timeout", True)
        raise TimeoutError(
            f"No 'completed' reply received in {timeout} seconds for correlation_id={correlation_id}, request_id={request_id}"
        )

def request_and_reply(
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
    import uuid
    from .commands import emit_command
    request_id = uuid.uuid4().hex
    traceparent = request_id
    emit_command(
        command_stream,
        correlation_id,
        saga_id,
        event_type,
        payload,
        request_id=request_id,
        traceparent=traceparent,
    )
    return read_replies(
        f"{response_prefix}:{correlation_id}",
        correlation_id,
        request_id,
        traceparent=traceparent,
        timeout=timeout,
        retry_strategy=exponential_retry(),
    )
