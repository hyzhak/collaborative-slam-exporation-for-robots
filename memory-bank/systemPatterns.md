# System Patterns

## Saga Pattern for Distributed Orchestration

- Uses the Saga pattern to coordinate a sequence of distributed tasks with compensation logic for failures.
- Each step is a Celery task; compensating actions are also tasks.
- Orchestrator coordinates the workflow, tracks state, and triggers compensations as needed.
- All state changes are persisted in PostgreSQL for traceability and rollback.

## Containerized Microservices

- Each component (worker, orchestrator, broker, DB, monitoring) runs in its own Docker container.
- Docker Compose (or Podman Compose) manages service startup, networking, and environment configuration.
- Flower provides real-time monitoring of Celery task execution.

## Integration Test Orchestration

- Integration tests are run in a dedicated container defined in `docker-compose.integration.yaml`.
- The integration test container depends on all core services (Redis, DB, Celery worker).
- The `tests/` directory is mounted as a volume into the integration test container, ensuring tests are always up-to-date with the codebase.
- Tests are executed using a helper script or directly via Podman Compose or Docker Compose commands.

## Observability and Traceability

- Flower UI for real-time task monitoring.
- All tasks and orchestrator steps log their actions, including saga_id for traceability.
- PostgreSQL stores workflow state and history for debugging and audit.
