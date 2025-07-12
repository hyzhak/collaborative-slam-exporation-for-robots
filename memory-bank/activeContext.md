# Active Context

## Current Work Focus

- Initializing the Memory Bank from the design.md document.
- Capturing project requirements, architecture, technology, and workflow context.
- Preparing for implementation: scaffolding docker-compose.yml, Dockerfile, requirements.txt, and Python app structure.

## Recent Changes

- Added RedisInsight service to docker-compose.yml for Redis Streams visualization; verified running at http://localhost:8001.

- Memory Bank files created: projectbrief.md, productContext.md, systemPatterns.md, techContext.md.
- All core context extracted from design.md and documented in memory-bank/.

## Next Steps

- Add official open-source Docker container to visualize Redis Streams (no tests required).
- Implement event-driven orchestrator: listen to incoming Redis Stream and invoke app/orchestrator.py.
- Refactor app/tasks.py so each Celery task emits its own Redis Stream event.
- Move orchestrator logic into Celery (e.g. using Canvas) for saga orchestration.
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
