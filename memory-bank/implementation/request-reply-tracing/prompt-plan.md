# Implementation Prompt Plan: Request-Reply Tracing

## Checklist

- [x] Add `read_replies` helper in `app/redis_utils.py`  
  **Status:** Completed. Implemented as async function in replies.py; tested in test_redis_utils.py.
- [x] Extend `emit_command` and `emit_event` to accept `maxlen` and `ttl`  
  **Status:** Completed. Implemented and tested in test_redis_utils.py.
- [x] Write unit tests for `read_replies` backoff, retry, and timeout  
  **Status:** Completed. test_redis_utils.py covers backoff, retry, timeout.
- [x] Implement all request-reply tasks (`allocate_resources`, `plan_route`, `perform_exploration`, `integrate_maps`) using generic `request_and_reply`  
  **Status:** Completed. request_and_reply used in tasks.py; tested in test_tasks_request_reply.py.
- [x] Write unified unit tests for all request-reply tasks in `test_tasks_request_reply.py`  
  **Status:** Completed. test_tasks_request_reply.py covers all.
- [x] Modify command handlers to emit multi-stage replies with full tracing fields  
  **Status:** Completed. Handlers use @multi_stage_reply; see allocate_resources.py and test_allocate_resources.py. Tracing fields present in test mocks.
- [x] Write unit tests for a handler’s multi-stage reply flow  
  **Status:** Completed. test_allocate_resources.py covers multi-stage reply sequence.
- [x] Update `command_listener.py` to propagate tracing metadata  
  **Status:** Completed. command_listener.py passes fields to handler; see test_command_listener_discovery.py.
- [x] Write unit tests for `command_listener` metadata propagation  
  **Status:** Completed. test_command_listener_discovery.py.
- [ ] Configure OpenTelemetry exporter for Tempo + Grafana and wrap `emit_command`/`read_replies` in spans  
  **Status:** Pending. No OTLP exporter or span-wrapping found in logging_config.py or celery_app.py.
- [x] Write integration tests (via `scripts/integration-tests.sh`) for full saga sunny-day flow and verify trace fields  
  **Status:** Completed. tests/integration/handlers/test_allocate_resources.py and related modules.
- [ ] Centralize configuration defaults and update README  
  **Status:** Pending. No evidence of centralized config or README update.
- [ ] Verify zero failures with `./scripts/unit-tests.sh` and `./scripts/integration-tests.sh`  
  **Status:** Pending. Manual verification required.

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

**Status:** Completed.  
- Handlers use @multi_stage_reply and emit “start”, “progress”, “completed” (see allocate_resources.py).  
- Unit test in test_allocate_resources.py asserts correct sequence and metadata.

Objective: Modify one command handler (e.g., `allocate_resources`) to emit multi-stage replies  
Guidance: In `app/command_handlers/handlers/allocate_resources.py`, extract `correlation_id`, `request_id`, `parent_span_id`, `traceparent` from message, emit a “start” reply, simulate work, emit a “progress” update, then a “completed” reply using `emit_event`.  
Test: Write a unit test that drives the handler by injecting a command record and asserting the sequence of XADD calls with correct metadata.  
Integration: Validates the reply-stream pattern at handler level.

### Prompt 6

**Status:** Completed.  
- command_listener.py passes all fields to handler.  
- test_command_listener_discovery.py verifies handler receives correct metadata.

Objective: Update `command_listener.py` to propagate tracing metadata and call handlers with full context  
Guidance: Adjust discovery logic to include trace fields in handler invocation parameters, ensure `emit_event` calls inherit those fields.  
Test: Write a unit test that mocks a command record and verifies the handler receives correct metadata.  
Integration: Connects low-level listener to tracing-enabled handlers.

### Prompt 7

**Status:** Pending.  
- No OTLP exporter or span-wrapping found in logging_config.py or celery_app.py.

Objective: Configure OpenTelemetry exporter and instrument key operations  
Guidance: In `app/logging_config.py` or `app/celery_app.py`, add OTLP exporter for Tempo + Grafana, and wrap calls to `emit_command`, `read_replies`, and handler entry in spans linked by `parent_span_id`.  
Test: Write a unit test using an in-memory exporter to assert spans are created and linked properly.  
Integration: Provides end-to-end observability for request/reply flows.

### Prompt 8

**Status:** Completed.  
- Integration tests in tests/integration/handlers/ validate multi-stage reply flow and trace fields.

Objective: Create an end-to-end integration test for the full saga using `scripts/integration-tests.sh`  
Guidance: Write a new test file under `tests/integration/` that triggers `app/orchestrator.py` with a sample area and robot count, consumes all multi-stage replies, and asserts final output and trace fields in Redis Streams.  
Test: Use the existing integration test script to automate setup and teardown, validate “start”, “progress”, and “completed” statuses and metadata.  
Integration: Confirms the complete pipeline functions as designed.

### Prompt 9

**Status:** Pending.  
- No evidence of centralized config or README update.  
- Manual test run required to confirm zero failures.

Objective: Final wiring and documentation update  
Guidance: Ensure configuration defaults (stream names, timeout, backoff, maxlen, ttl) are centralized in a config module or environment variables, update project README with usage examples, and verify all tests pass.  
Test: Run `./scripts/unit-tests.sh` and `./scripts/integration-tests.sh` and confirm zero failures.  
Integration: Completes the feature rollout and documentation for maintainers.
