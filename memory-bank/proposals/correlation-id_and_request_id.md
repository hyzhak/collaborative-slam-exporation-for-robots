## Saga Correlation and Tracing Design Document

### 1. Purpose and Scope

This document describes a standardized approach for propagating **correlation\_id** and managing intermediate **request/reply** interactions in a Redis Streams–based saga orchestration. It covers:

* End-to-end traceability across asynchronous events
* Local request identification within sub-flows
* Hierarchical tracing concepts (trace/span relationships)
* Implementation patterns and best practices

### 2. Background and Motivation

In distributed, event-driven architectures, maintaining visibility over a long-running transaction (saga) is critical for:

* Monitoring progress and performance
* Troubleshooting failures and timeouts
* Auditing and compliance

A single **correlation\_id** per saga, combined with per-call **request\_id** or **span\_id**, mirrors industry standards (e.g., W3C Trace Context, OpenTelemetry) and enables full lifecycle tracking.

### 3. Correlation ID Strategy

1. **Generate Once**: Create a UUID4 at the saga entry point and assign it to every event in the workflow.
2. **Propagate**: Include `correlation_id` in every Redis Stream record (via `XADD` fields) and service call header.
3. **Standardize Format**: Use the W3C Trace Context `trace_id` format (32-hex characters) for compatibility.

### 4. Request/Reply Sub-Correlation

Within any saga step that invokes a request/reply:

* **request\_id**: Generate a new UUID for each request to match replies accurately.
* **Echo on Reply**: The reply must include the same `request_id` for binding.
* **Inherit correlation\_id**: Carry the saga’s `correlation_id` in both request and reply.

```redis
XADD request-stream * correlation_id <trace_id> request_id <span_id> action "reserve-credit"
XADD reply-stream  * correlation_id <trace_id> request_id <span_id> status "approved"
```

### 5. Hierarchical Tracing Model

* **trace\_id** = saga-level `correlation_id`
* **span\_id** = per-request `request_id`
* **parent\_span\_id** = links a child span back to its caller

Adopt the W3C **`traceparent`** header format:

```
traceparent: 00-<trace_id>-<span_id>-01
```

This enables existing OpenTelemetry agents and dashboards to ingest and visualize call trees.

### 6. Redis Streams Implementation Patterns

* **Field-Value Metadata**: Store trace IDs directly in stream entries for easy access by consumers.
* **Consumer Groups**: Use Redis Stream consumer groups to parallelize processing while retaining metadata context.
* **Key Naming**: Name streams and groups consistent with domain and version info (e.g., `order.saga.v1`), but do not rely on stream name for correlation.

### 7. Example Workflow

1. **Start Saga**: `XADD saga-stream * correlation_id=<t1> action=start order_id=123`
2. **Reserve Inventory**:

   * Request: `XADD inv-req * correlation_id=<t1> request_id=<s1> item_id=XYZ qty=10`
   * Reply:  `XADD inv-resp* correlation_id=<t1> request_id=<s1> status=ok`
3. **Process Payment**: repeat with new span\_id `<s2>`
4. **Finalize**: update saga state and emit `completed` event with `correlation_id=<t1>`.

### 8. Best Practices & Recommendations

* **Keep IDs Immutable**: Never modify IDs in-transit; generate fresh span\_ids for each logical call.
* **Limit Payload Size**: Only include trace metadata fields, avoid large headers or values.
* **Use Observability Tools**: Integrate with OpenTelemetry or Jaeger to capture, store, and visualize traces.
* **Document Conventions**: Maintain a shared style guide for ID formats, header names, and stream naming.

### 9. References

1. W3C Trace Context Specification: [https://www.w3.org/TR/trace-context/](https://www.w3.org/TR/trace-context/)
2. OpenTelemetry Trace API & SDK: [https://opentelemetry.io/](https://opentelemetry.io/)
3. Redis Streams Documentation: [https://redis.io/docs/data-types/streams/](https://redis.io/docs/data-types/streams/)
4. Eventuate Tram Sagas Pattern: [https://eventuate.io/docs/](https://eventuate.io/docs/)
5. AsyncAPI Request/Reply Tutorial: [https://www.asyncapi.com/docs/tutorials/](https://www.asyncapi.com/docs/tutorials/)
6. MassTransit Saga Documentation: [https://masstransit.io/documentation/](https://masstransit.io/documentation/)
