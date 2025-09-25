# Collaborative SLAM Exploration for Robots

A proof-of-concept that demonstrates how Celery, Redis Streams, and async command handlers can implement the Saga pattern for collaborative robot exploration. The project coordinates mission phases—resource allocation, route planning, exploration, and map integration—while providing compensating actions and rich telemetry.

- **Saga orchestration:** The Celery flow builds a canvas of mission tasks with compensations using `link_error`. 【F:app/flows/mission_start_celery/orchestrator.py†L27-L50】
- **Redis-backed services:** Celery tasks exchange commands and replies with async handlers via Redis Streams. 【F:app/flows/mission_start_celery/tasks.py†L18-L75】
- **Async command bus:** The listener discovers handlers dynamically and manages consumer groups for each mission stream. 【F:app/commands/listener.py†L18-L109】
- **Observability:** Flower consumes Celery events while handlers emit start/progress/completed telemetry for dashboards. 【F:docker-compose.yml†L23-L34】【F:app/redis_utils/decorators.py†L24-L55】

Comprehensive architecture and lessons learned are available in the [`docs/`](docs) folder.

## Repository Layout

```
app/
├── celery_app.py                # Celery configuration and Redis readiness probe
├── commands/                    # Redis stream listener and handler implementations
├── flows/                       # Celery and async saga orchestrators
└── redis_utils/                 # Request/reply helpers and telemetry decorators
docker-compose.yml               # Container stack for Redis, PostgreSQL, Celery, Flower, RedisInsight
Dockerfile                       # Runtime image for Celery worker and listener
docs/                            # High-level architecture and lessons learned
scripts/                         # Helper scripts for local automation
tests/                           # Unit and integration suites (pytest)
```

## Getting Started

### Prerequisites

- Docker and Docker Compose (v2 syntax)
- Optional: Python 3.11+ if you wish to run tests without containers

### Launch the Stack

1. Clone the repository and move into the project directory.
2. Start all services:

   ```bash
   docker compose up --build
   ```

   This command launches Redis, PostgreSQL, the Celery worker, the Redis stream listener, Flower, and RedisInsight. Health checks ensure Redis is available before Celery starts. 【F:docker-compose.yml†L1-L74】

3. Watch logs for the `orchestrator` service to confirm the listener is consuming `mission:commands` events.

### Trigger a Mission

Publish a `mission:start` command to Redis Streams. The required fields are documented in the mission handler. 【F:app/commands/handlers/start_mission.py†L24-L47】

```bash
docker compose exec redis redis-cli XADD mission:commands * \
  event_type mission:start \
  correlation_id demo-1 \
  robot_count 2 \
  area ZoneA \
  reply_stream mission:replies:demo-1 \
  backend celery
```

Monitor Flower at [http://localhost:5555](http://localhost:5555) and RedisInsight at [http://localhost:8001](http://localhost:8001) to follow task progress and stream telemetry.

### Shutting Down

```bash
docker compose down
```

Use `docker compose down -v` if you wish to remove the Postgres volume.

## Testing

The project ships with pytest-based unit and integration tests.

- **Unit tests:** Exercise handlers, Redis utilities, and the async orchestrator. 【F:tests/unit/flow/test_async_orchestrator.py†L1-L120】【F:tests/unit/test_tasks_request_reply.py†L1-L86】
- **Integration tests:** Interact with Redis Streams to validate end-to-end orchestration. 【F:tests/integration/test_orchestrator_trigger.py†L1-L88】

Run the suites locally using the development compose file:

```bash
docker compose -f docker-compose.unit.yaml up --build lint unit_test
```

For integration testing inside containers:

```bash
./scripts/integration-tests.sh
```

Both commands rely on the dev image defined in `Dockerfile.dev` and enforce linting via Ruff.

## Documentation

- [High-Level Architecture](docs/high_level_design.md)
- [Lessons Learned and Implementation Playbook](docs/lessons_learned.md)

These documents contain detailed diagrams, step-by-step guidance, and testing considerations for replicating the architecture.

## Contributing

Contributions are welcome. Please open an issue describing the enhancement or bug before submitting a pull request, and follow the existing linting/testing workflow.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

