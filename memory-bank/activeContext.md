# Active Context

## Current Work Focus

- Implement event-driven orchestrator: listen to incoming Redis Stream and invoke app/orchestrator.py.

## Recent Changes

- Introduced event-driven orchestration: orchestrator service now runs app/orchestrator_listener.py, listening to Redis Streams and triggering saga workflows.
- Added centralized logging configuration (app/logging_config.py) for consistent, configurable logs across all services.
- Refactored saga orchestration logic in app/orchestrator.py to support event-driven invocation and robust compensation.
- All saga steps and compensation logic implemented as Celery tasks in app/tasks.py, with improved logging and testability.
- Enhanced Celery app startup reliability in app/celery_app.py (waits for Redis).
- Added integration test (tests/test_orchestrator_trigger.py) to validate end-to-end event-driven orchestration via Redis Streams.
- docker-compose.yml and docker-compose.test.yaml updated: new orchestrator service, RedisInsight, Flower, and integration_test service for CI.
- Added RedisInsight service to docker-compose.yml for Redis Streams visualization; verified running at <http://localhost:8001>.
- Memory Bank files created: projectbrief.md, productContext.md, systemPatterns.md, techContext.md.
- All core context extracted from design.md and documented in memory-bank/.

## Next Steps

- Move orchestrator logic into Celery using Canvas primitives for saga orchestration (not yet implemented).
- For each item, follow TDD:
  1. Write integration tests.
  2. Run tests (should fail).
  3. Implement feature.
  4. Run tests (should pass).
  5. Update Memory Bank notes.
  6. Commit changes.

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
