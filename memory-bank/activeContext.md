# Active Context

## Current Work Focus

- Implement event-driven orchestrator: listen to incoming Redis Stream and invoke app/orchestrator.py.

## Next Steps

- Implement FastAPI HTTP API for triggering Saga orchestrations.

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
