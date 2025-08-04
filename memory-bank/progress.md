# Progress Log

## Recent Milestones

### 2025-08-03: Request-Reply Tracing Implementation Review

- All handler integration tests exist and pass as designed. Each handler emits “start → progress → completed” as required.
- Stream names, groups, and event types align with the original plan.
- Integration tests in `tests/integration/handlers/` confirm correct sequence and metadata.
- One test module per handler exists; focus is on multi-stage replies, not business logic.
- Shared utilities in `tests/integration/handlers/utils.py` are implemented and used.
- Assertions and file structure match the plan.
- Remaining gaps: OpenTelemetry exporter and span-wrapping not implemented; config centralization and README update pending; manual test run required for final verification.

- Removed legacy single-task Celery saga tests in favor of unified parameterized test_tasks_request_reply.py for all request-reply saga tasks.
- Added `read_replies` helper to `app/redis_utils.py` supporting blocking reply stream reads via XREADGROUP, consumer group best practices, and pluggable retry strategies (exponential, linear, immediate fail). Updated activeContext.md and prompt plan to reflect new implementation and requirements.
- Refactored command listener and handler discovery: moved handlers to app/command_handlers/handlers/, updated all references, and validated with passing unit tests.
- Redis Streams are now used for all event-driven orchestration and command/event propagation.
- All event/command emission uses only top-level fields: `correlation_id`, `saga_id`, `event_type`, `status` (for events), `payload`, and `timestamp`.
- The `domain` field has been removed from all event/command emissions and function signatures for simplicity.
- A persistent `correlation_id` is required and propagated through all events and commands, enabling tracking of related sagas.
- Integration test (tests/test_orchestrator_trigger.py) validates that correlation_id is correctly propagated end-to-end.
- Event-driven orchestration implemented: orchestrator service now listens to Redis Streams and triggers saga workflows via modular command handlers.
- Centralized logging configuration (app/logging_config.py) adopted across all services.
- Saga orchestration logic refactored for event-driven flow and robust compensation (app/orchestrator.py).
- All saga steps and compensation logic implemented as Celery tasks with improved logging (app/tasks.py).
- Celery app startup reliability improved (app/celery_app.py waits for Redis).
- docker-compose.yml and docker-compose.integration.yaml updated: orchestrator service, RedisInsight, Flower, and integration_test service for CI.
- Added RedisInsight service for Redis Streams visualization; verified running at http://localhost:8001.
- Initial implementation of Saga orchestration with Celery, Redis, and PostgreSQL.
- Added Flower for real-time monitoring of task execution.
- Docker Compose setup for all core services.
- Implemented compensation logic for robust rollback on failures.
- Refactored orchestrator and tasks for clarity and maintainability.
