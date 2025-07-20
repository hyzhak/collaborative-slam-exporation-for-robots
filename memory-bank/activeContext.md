# Active Context

## Current Work Focus

- Added `read_replies` helper to `app/redis_utils.py` for blocking reply stream reads using XREADGROUP, consumer group best practices, and pluggable retry strategies (exponential, linear, or immediate fail).
- Refactored command listener and handler discovery: moved handlers to app/command_handlers/handlers/, updated all references, and validated with passing unit tests.
- Implement event-driven orchestrator: listen to incoming Redis Stream and invoke app/orchestrator.py.

## Next Steps

- Extend `read_replies` unit tests to cover retry strategies and timeout handling.
- Develop additional handler modules under app/command_handlers/handlers/.
- Extend integration tests for end-to-end command stream handling.

## Active Decisions and Considerations

- Using orchestration-based Saga with explicit compensation for rollback.
- All services containerized for reproducibility and ease of deployment.
- Single Postgres instance for all tasks (simplified for PoC).
- Optional FastAPI for HTTP-triggered orchestration.

## Important Patterns and Preferences

- saga_id used for traceability in all tasks and logs.
- Logging and monitoring prioritized for debugging and demonstration.
- Docker Compose as the primary orchestration tool.

## Learnings and Project Insights

- Celery and Flower provide sufficient primitives for Saga orchestration and monitoring.
- Explicit compensation logic is required for rollback; no built-in distributed transaction support.
- Docker Compose simplifies multi-service setup and teardown.
