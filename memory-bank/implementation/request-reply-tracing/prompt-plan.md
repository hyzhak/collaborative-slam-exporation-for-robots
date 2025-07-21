# Implementation Prompt Plan: Request-Reply Tracing

## Checklist

- [x] Add `read_replies` helper in `app/redis_utils.py`
- [x] Extend `emit_command` and `emit_event` to accept `maxlen` and `ttl`
- [x] Write unit tests for `read_replies` backoff, retry, and timeout
- [x] Implement all request-reply tasks (`allocate_resources`, `plan_route`, `perform_exploration`, `integrate_maps`) using generic `request_and_reply`
- [x] Write unified unit tests for all request-reply tasks in `test_tasks_request_reply.py`
- [ ] Modify command handlers to emit multi-stage replies with full tracing fields
- [ ] Write unit tests for a handler’s multi-stage reply flow
- [ ] Update `command_listener.py` to propagate tracing metadata
- [ ] Write unit tests for `command_listener` metadata propagation
- [ ] Configure OpenTelemetry exporter for Tempo + Grafana and wrap `emit_command`/`read_replies` in spans
- [ ] Write integration tests (via `scripts/integration-tests.sh`) for full saga sunny-day flow and verify trace fields
- [ ] Centralize configuration defaults and update README
- [ ] Verify zero failures with `./scripts/unit-tests.sh` and `./scripts/integration-tests.sh`

---

## Prompt Plan

### Prompt 1:  **Status: Completed & Tested**

Objective: Scaffold a blocking-reply reader in `app/redis_utils.py`  
Guidance: Create a new function `read_replies(stream, correlation_id, request_id, timeout, backoff_config)` that:

- Initializes a consumer group on the given `stream` (creating it with `XGROUP CREATE` and `mkstream=True` if needed) using a group name derived from the stream (for example, `<stream>:group`) and a unique consumer name (for example, `reader-<UUID>`), following Redis Streams best practices.
- Uses `XREADGROUP` with `BLOCK` to read new entries from the reply stream.
- Applies exponential backoff on empty reads with a default `backoff_config` (initial_delay=0.1s, max_delay=1s, factor=2), then continues retrying until the total `timeout` is exceeded, at which point it raises a `TimeoutError`.
- Logs any `"start"` and `"progress"` messages internally but returns only the `"completed"` reply message as a dictionary containing all stream fields.
Test: Write a unit test that simulates no messages in the stream and verifies backoff retries and eventual timeout exception using the default backoff configuration.  
Integration: This helper will be the foundation for all tasks’ reply handling.

### Prompt 2

Objective: Extend `emit_command` and `emit_event` to accept optional `maxlen` and `ttl` parameters  
Guidance: Update signatures to include `maxlen=None, ttl=None`, apply `XADD MAXLEN ~ maxlen` when provided, and call `EXPIRE` on the stream.  
Test: Write unit tests that emit to a temporary Redis instance, assert stream length trimming and TTL setting.  
Integration: Enables resource-bounded streams used across commands and replies.

### Prompt 3–4:  **Status: Completed (generic request-reply pattern)**

Objective: Implement all request-reply tasks using the generic `request_and_reply` helper in `app/tasks.py`.
Guidance: Each task emits its command and blocks for the completed reply using `request_and_reply`, which handles UUID generation, tracing metadata, and reply reading.
Test: Unified unit tests in `test_tasks_request_reply.py` mock `request_and_reply` and verify correct event emission and reply handling for all tasks.
Integration: Ensures DRY, consistent request-reply logic across all saga steps.

### Prompt 5

Objective: Modify one command handler (e.g., `allocate_resources`) to emit multi-stage replies  
Guidance: In `app/command_handlers/handlers/allocate_resources.py`, extract `correlation_id`, `request_id`, `parent_span_id`, `traceparent` from message, emit a “start” reply, simulate work, emit a “progress” update, then a “completed” reply using `emit_event`.  
Test: Write a unit test that drives the handler by injecting a command record and asserting the sequence of XADD calls with correct metadata.  
Integration: Validates the reply-stream pattern at handler level.

### Prompt 6

Objective: Update `command_listener.py` to propagate tracing metadata and call handlers with full context  
Guidance: Adjust discovery logic to include trace fields in handler invocation parameters, ensure `emit_event` calls inherit those fields.  
Test: Write a unit test that mocks a command record and verifies the handler receives correct metadata.  
Integration: Connects low-level listener to tracing-enabled handlers.

### Prompt 7

Objective: Configure OpenTelemetry exporter and instrument key operations  
Guidance: In `app/logging_config.py` or `app/celery_app.py`, add OTLP exporter for Tempo + Grafana, and wrap calls to `emit_command`, `read_replies`, and handler entry in spans linked by `parent_span_id`.  
Test: Write a unit test using an in-memory exporter to assert spans are created and linked properly.  
Integration: Provides end-to-end observability for request/reply flows.

### Prompt 8

Objective: Create an end-to-end integration test for the full saga using `scripts/integration-tests.sh`  
Guidance: Write a new test file under `tests/integration/` that triggers `app/orchestrator.py` with a sample area and robot count, consumes all multi-stage replies, and asserts final output and trace fields in Redis Streams.  
Test: Use the existing integration test script to automate setup and teardown, validate “start”, “progress”, and “completed” statuses and metadata.  
Integration: Confirms the complete pipeline functions as designed.

### Prompt 9

Objective: Final wiring and documentation update  
Guidance: Ensure configuration defaults (stream names, timeout, backoff, maxlen, ttl) are centralized in a config module or environment variables, update project README with usage examples, and verify all tests pass.  
Test: Run `./scripts/unit-tests.sh` and `./scripts/integration-tests.sh` and confirm zero failures.  
Integration: Completes the feature rollout and documentation for maintainers.
