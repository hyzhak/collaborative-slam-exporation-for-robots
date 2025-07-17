# Redis Streams Request/Reply Pattern with Multi‑Stage Replies

## 1. Overview

This document describes a canonical design for implementing a request/reply protocol on top of Redis Streams, extended to support multi‑stage status updates (e.g., `start`, `progress`, `completed`). It provides:

* **Core concepts** behind Redis Streams
* **Detailed flow** for single‑ and multi‑stage replies
* **Reference implementation** in Python (`redis-py`)
* **Best practices** from Redis team and community
* **Key resources** for further reading

---

## 2. Core Concepts

### 2.1 Immutable, Append‑Only Log

* Redis Streams act as an append‑only sequence of entries (no in‑place updates).
* Every call to `XADD` creates a new, time‑ordered entry with a unique ID.

### 2.2 Consumer Groups & Acknowledgment

* **Consumer groups** (`XGROUP CREATE`, `XREADGROUP`) allow multiple workers to share work.
* **Pending Entries List** (PEL) tracks unacknowledged messages.
* `XACK` removes processed IDs from the PEL, preventing redelivery.

### 2.3 Blocking & Non‑Blocking Reads

* Clients/workers can block waiting for new entries via `XREAD BLOCK` or `XREADGROUP … BLOCK`.
* Use the `isolated` option on `XREADGROUP` to avoid pipeline side‑effects.

---

## 3. Multi‑Stage Replies

Instead of a single final reply, clients often need updates at various stages:

1. **start**: Worker acknowledges receipt and begins processing.
2. **progress**: Periodic updates (e.g., 25%, 50%, 75%).
3. **completed**: Final result.

### 3.1 Message Fields

* `correlationId`: UUID per request, ties stages to one workflow.
* `status` (or `event`): One of `start` | `progress` | `completed`.
* `progress` (optional): Numeric percentage for progress updates.
* `payload` / `result`: Data carried by the message.

### 3.2 Streams Layout

* **Request stream**: `service:requests`
* **Reply stream**: Unique per request, e.g. `service:responses:<correlationId>`

Clients block on their reply stream to receive all stages in order.

---

## 4. Reference Implementation (Python)

### 4.1 Client Code

```python
import redis, uuid

def send_request(payload, timeout_ms=5000):
    corr_id      = uuid.uuid4().hex
    req_stream   = "service:requests"
    reply_stream = f"service:responses:{corr_id}"

    # Enqueue the request (no status emitted by client)
    r = redis.Redis()
    r.xadd(req_stream, {
        "payload": payload,
        "correlationId": corr_id,
        "replyTo": reply_stream
    })

    # Listen on reply stream for all stages
    messages = r.xread({reply_stream: "0-0"}, block=timeout_ms)
    for _, entries in messages:
        for _, msg in entries:
            status = msg["status"]
            # Handle start/progress/completed
            print(f"[{status}]", msg)
```

### 4.2 Worker Code

```python
import redis, time, uuid

r = redis.Redis()
stream   = "service:requests"
group    = "requests-group"
consumer = f"worker-{uuid.uuid4().hex}"  # unique consumer name

# Ensure consumer group exists
try:
    r.xgroup_create(stream, group, id="0", mkstream=True)
except redis.exceptions.ResponseError:
    pass  # group may already exist

while True:
    # Read new requests
    entries = r.xreadgroup(group, consumer,
                           {stream: ">"}, count=1, block=0)
    if not entries:
        continue

    _, msgs = entries[0]
    for msg_id, msg in msgs:
        corr_id     = msg[b"correlationId"].decode()
        reply_stream= msg[b"replyTo"].decode()
        payload     = msg[b"payload"].decode()

        # 1) Signal start
        r.xadd(reply_stream, {
            "correlationId": corr_id,
            "status":        "start"
        })

        # 2) Simulate work with progress updates
        for pct in (25, 50, 75):
            time.sleep(0.5)
            r.xadd(reply_stream, {
                "correlationId": corr_id,
                "status":        "progress",
                "progress":      pct
            })

        # 3) Final result
        result = do_work(payload)
        r.xadd(reply_stream, {
            "correlationId": corr_id,
            "status":        "completed",
            "result":        result
        })

        # 4) Acknowledge the request
        r.xack(stream, group, msg_id)
```

---

## 5. Best Practices & Tips

* **Dedicated reply streams**: Avoid scanning large shared streams; use one per request or per client.
* **Key naming**: Use readable, colon‑separated prefixes (`service:requests`, `service:responses:<id>`).
* **Trim large streams**: `XADD MAXLEN ~ <count>` to cap memory use.
* **Monitor PEL**: `XPENDING` and `XAUTOCLAIM` to handle stuck messages.
* **Use `isolated`** on `XREADGROUP` for safe blocking reads in pipelines.

---

## 6. Resources

* **Redis Streams Documentation**: [https://redis.io/docs/data-types/streams/](https://redis.io/docs/data-types/streams/)
* **Official Redis Blog**: Introduction to Redis Streams tutorial
* **Redis Community**: Best practices thread on multi‑stage streaming
* **Server‑Sent Events Spec** (analogy): [https://html.spec.whatwg.org/multipage/server-sent-events.html](https://html.spec.whatwg.org/multipage/server-sent-events.html)
* **StackOverflow Examples**: Typical request/reply implementations
