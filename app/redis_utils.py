import os
import redis
import json
import time
import uuid
import logging

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))


def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def emit_command(
    stream,
    correlation_id,
    saga_id,
    event_type,
    payload,
    request_id=None,
    traceparent=None,
    maxlen=None,
    ttl=None,
):
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    if request_id is not None:
        fields["request_id"] = request_id
    if traceparent is not None:
        fields["traceparent"] = traceparent
    xadd_kwargs = {}
    if maxlen is not None:
        xadd_kwargs["maxlen"] = maxlen
        xadd_kwargs["approximate"] = True
    entry_id = r.xadd(stream, fields, **xadd_kwargs)
    if ttl is not None:
        r.expire(stream, ttl)
    return entry_id


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
    except redis.exceptions.ResponseError as e:
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
    raise TimeoutError(
        f"No 'completed' reply received in {timeout} seconds for correlation_id={correlation_id}, request_id={request_id}"
    )


def emit_event(
    stream, correlation_id, saga_id, event_type, status, payload, maxlen=None, ttl=None
):
    r = get_redis_client()
    fields = {
        "correlation_id": correlation_id,
        "saga_id": saga_id,
        "event_type": event_type,
        "status": status,
        "payload": json.dumps(payload),
        "timestamp": str(int(time.time())),
    }
    xadd_kwargs = {}
    if maxlen is not None:
        xadd_kwargs["maxlen"] = maxlen
        xadd_kwargs["approximate"] = True
    entry_id = r.xadd(stream, fields, **xadd_kwargs)
    if ttl is not None:
        r.expire(stream, ttl)
    return entry_id


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

def immediate_fail_retry(attempt, elapsed, last_delay):
    """
    Retry strategy: fail immediately, no retries.
    """
    return None


def exponential_retry(initial=0.1, factor=2, max_delay=1.0, max_attempts=10):
    """
    Factory for exponential backoff retry strategy.
    Returns a function (attempt, elapsed, last_delay) -> delay or None.
    """

    def strategy(attempt, elapsed, last_delay):
        if attempt > max_attempts:
            return None
        try:
            delay = initial * (factor ** (attempt - 1))
        except OverflowError:
            return None
        return min(delay, max_delay)

    return strategy


def linear_retry(step=0.2, max_delay=1.0, max_attempts=10):
    """
    Factory for linear backoff retry strategy.
    Returns a function (attempt, elapsed, last_delay) -> delay or None.
    """

    def strategy(attempt, elapsed, last_delay):
        if attempt > max_attempts:
            return None
        try:
            delay = step * attempt
        except OverflowError:
            return None
        return min(delay, max_delay)

    return strategy
