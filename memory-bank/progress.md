# Progress Log

## Recent Milestones

- Redis Streams are now used for all event-driven orchestration and command/event propagation.
- All event/command emission uses only top-level fields: `correlation_id`, `saga_id`, `event_type`, `status` (for events), `payload`, and `timestamp`.
- The `domain` field has been removed from all event/command emissions and function signatures for simplicity.
- A persistent `correlation_id` is required and propagated through all events and commands, enabling tracking of related sagas.
- Integration test (tests/test_orchestrator_trigger.py) validates that correlation_id is correctly propagated end-to-end.
- Event-driven orchestration implemented: orchestrator service now listens to Redis Streams and triggers saga workflows via app/orchestrator_listener.py.
- Centralized logging configuration (app/logging_config.py) adopted across all services.
- Saga orchestration logic refactored for event-driven flow and robust compensation (app/orchestrator.py).
- All saga steps and compensation logic implemented as Celery tasks with improved logging (app/tasks.py).
- Celery app startup reliability improved (app/celery_app.py waits for Redis).
- docker-compose.yml and docker-compose.test.yaml updated: orchestrator service, RedisInsight, Flower, and integration_test service for CI.
- Added RedisInsight service for Redis Streams visualization; verified running at http://localhost:8001.
- Initial implementation of Saga orchestration with Celery, Redis, and PostgreSQL.
- Added Flower for real-time monitoring of task execution.
- Docker Compose setup for all core services.
- Implemented compensation logic for robust rollback on failures.
- Added optional FastAPI endpoint for triggering Sagas.
- Refactored orchestrator and tasks for clarity and maintainability.
