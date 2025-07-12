# Tech Context

## Technologies Used

- Python 3.11 (Celery tasks, orchestrator, optional FastAPI)
- Celery (asynchronous task queue and orchestration)
- Redis (Celery broker and result backend)
- PostgreSQL (shared persistent state for tasks)
- Docker & Docker Compose (containerization and orchestration)
- Flower (Celery monitoring UI)
- (Optional) FastAPI + Uvicorn (HTTP API for triggering Saga)

## Development Setup

- All components run as Docker containers managed by docker-compose.
- Environment variables configure service connections (broker, DB).
- Source code organized under an `app/` Python package.

## Technical Constraints

- All dependencies must be open-source and run on a single Ubuntu server.
- No distributed transactions; all rollback via explicit compensation logic.
- Single Postgres instance for simplicity (not per-service DBs).

## Dependencies

- celery
- redis
- flower
- psycopg2-binary
- SQLAlchemy (optional, for ORM)
- fastapi, uvicorn (optional, for API)

## Tool Usage Patterns

- Celery tasks registered in `app/tasks.py`, orchestrator logic in `app/orchestrator.py`.
- Docker Compose manages service startup order and networking.
- Flower connects to Redis to visualize task execution.
- All logs and saga_id values used for traceability and debugging.

## Testing Infrastructure

- Integration tests are defined in the `tests/` directory.
- Automated integration tests run in a dedicated container using `docker-compose.test.yaml`.
- Tests can be executed via:
  - `./scripts/integration-tests.sh` (helper script)
  - `podman-compose -f docker-compose.yml -f docker-compose.test.yaml run integration_test`
  - `docker-compose -f docker-compose.yml -f docker-compose.test.yaml up --build --exit-code-from integration_test integration_test`
- The `tests/` directory is mounted as a volume into the integration test container.
- All code changes must be validated by running the integration test suite before merging or deployment.
