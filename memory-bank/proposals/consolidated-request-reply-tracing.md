# Consolidated Design: Modular Request/Reply & Tracing for Redis Streams Saga Orchestration

## 1. Purpose & Scope

This document unifies the request/reply pattern and correlation/tracing conventions for distributed saga orchestration using Redis Streams and Celery. It provides a modular, extensible approach for Python-based orchestrators and handlers, ensuring traceability, observability, and maintainability across workflows.

---

## 2. Architectural Overview

- **Redis Streams**: Used for command and reply/event propagation. Streams are immutable, append-only logs supporting consumer groups and blocking/non-blocking reads.
- **Celery Saga Orchestrator**: Chains tasks (allocate_resources, plan_route, etc.), passing correlation and saga IDs through each step.
- **Handlers**: Listen on command streams, process requests, and emit multi-stage replies.

---

## 3. Correlation & Trace Context

- **correlation_id**: UUID4, generated at saga entry, propagated through all events and stream records. Serves as the saga-level trace_id.
- **request_id**: UUID4, generated per request/reply, used as span_id for hierarchical tracing.
- **parent_span_id**: Links child spans to their parent operation.
- **traceparent**: W3C Trace Context format: `00-<correlation_id>-<request_id>-01`
- **Field Naming**: Use snake_case for all fields (correlation_id, request_id, parent_span_id, traceparent, status, etc.).

**Propagation Rules:**

- Always include correlation_id, request_id, parent_span_id (if applicable), and traceparent in every stream entry.
- IDs are immutable; generate new span IDs for each logical call.

---

## 4. Modular Request/Reply Pattern

- **Command Streams**: e.g., `resources:commands`, `routing:commands`
- **Reply Streams**: Dedicated per request or per saga, e.g., `service:responses:<correlation_id>` or `service:responses:<correlation_id>:<request_id>`
- **Multi-Stage Replies**:  
  - `start`: Worker acknowledges receipt and begins processing.  
  - `progress`: Periodic updates (e.g., 25%, 50%, 75%).  
  - `completed`: Final result.

**Message Schema Example:**

```json
{
  "correlation_id": "<uuid>",
  "request_id": "<uuid>",
  "parent_span_id": "<uuid>",
  "traceparent": "00-<correlation_id>-<request_id>-01",
  "status": "progress",
  "progress": 50,
  "result": "...",
  "payload": "...",
  "timestamp": "<unix>"
}
```

---

## 5. Utility Library Design

- **redis_utils.py**:
  - `emit_command(stream, correlation_id, saga_id, event_type, payload)`
  - `emit_event(stream, correlation_id, saga_id, event_type, status, payload)`
  - **Enhancement**: Add helper for blocking reply stream reads with timeout, and support for MAXLEN trimming/TTL.

---

## 6. Task Implementation Guidelines

- Each Celery task:
  - Receives correlation_id and saga_id.
  - Generates request_id for each command emission.
  - Emits command with full tracing metadata.
  - Waits for and processes multi-stage replies.
  - Returns result with tracing context.

**Template:**

```python
def task_fn(correlation_id, saga_id, ...):
    request_id = uuid.uuid4().hex
    parent_span_id = ... # if applicable
    traceparent = f"00-{correlation_id}-{request_id}-01"
    emit_command(
        stream,
        correlation_id,
        saga_id,
        event_type,
        {
            "request_id": request_id,
            "parent_span_id": parent_span_id,
            "traceparent": traceparent,
            ...
        }
    )
    # Listen for replies on reply stream
    # Process start/progress/completed
```

---

## 7. Handler & Listener Integration

- **Command Handlers**:
  - Listen on their respective command streams.
  - For each message, extract tracing metadata.
  - Emit multi-stage replies to the specified reply stream, including all tracing fields.
  - Use consumer groups for parallelism and reliability.

- **Command Listener**:
  - Discovers handler modules.
  - Asynchronously reads and processes messages, acknowledging with xack.

---

## 8. Best Practices & Operational Concerns

- **Stream Trimming**: Use `XADD MAXLEN ~ <count>` or TTL to cap memory usage.
- **PEL Management**: Monitor pending entries, use `XPENDING` and `XAUTOCLAIM` for stuck messages.
- **Observability**: Integrate OpenTelemetry by propagating traceparent and parent_span_id.
- **Immutability**: Never modify IDs in-transit.
- **Payload Limits**: Only include essential trace metadata.
- **Style Guide**: Maintain conventions for field names, header formats, and stream naming.

---

## 9. References

- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Trace API & SDK](https://opentelemetry.io/)
- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [Eventuate Tram Sagas Pattern](https://eventuate.io/docs/)
- [AsyncAPI Request/Reply Tutorial](https://www.asyncapi.com/docs/tutorials/)
- [MassTransit Saga Documentation](https://masstransit.io/documentation/)
