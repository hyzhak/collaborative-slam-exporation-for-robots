# Handler Integration Tests Design

## 1. Purpose

Define end-to-end integration tests that verify each command handler listens on its Redis stream and emits a “start → progress → completed” sequence against a live Redis service.

## 2. Infrastructure

- Docker Compose environment (uses `redis://redis:6379/0`).
- Tests run as a separate service under `docker-compose.integration.yaml`.
- Reuses existing Redis and orchestrator listener service.

## 3. Test Scope

- One test module per handler (allocate, integrate, perform, plan, release).
- Focus on multi-stage replies only; business logic verification (e.g., sleep) is out of scope.

## 4. Shared Utilities (`tests/integration/handlers/utils.py`)

- `redis_client` fixture (synchronous `redis.Redis`).
- `send_command(stream, event_type, correlation_id, saga_id, extra_fields=None)`: XADD command stream.
- `collect_events(stream, group, correlation_id, expected_statuses, timeout)`: XREADGROUP loop collecting statuses.

## 5. Stream & Handler Matrix

| Handler             | Stream               | Group                     | Event Type          |
| ------------------- | -------------------- | ------------------------- | ------------------- |
| allocate_resources  | resources:commands   | resources_handler_group   | resources:allocate  |
| integrate_maps      | map:commands         | map_handler_group         | map:integrate       |
| perform_exploration | exploration:commands | exploration_handler_group | exploration:perform |
| plan_route          | routing:commands     | routing_handler_group     | routing:plan        |
| release_resources   | resources:commands   | resources_handler_group   | resources:release   |

## 6. Test Flow (per module)

1. Create a dedicated consumer group for reply stream (e.g., `<stream>:integration_test_group`) to avoid interference with groups used by the orchestrator or listeners.
2. Generate unique `correlation_id`, `saga_id`.
3. Call `send_command(...)`.
4. Call `collect_events(...)` expecting `["start","progress","completed"]` using the dedicated group.
5. Assert correct order and payload fields (fraction increases, matching IDs).

## 7. Assertions

- First status == “start”
- At least one progress with `fraction` > 0 and ≤ 1
- Final status == “completed”

## 8. File Structure

```
memory-bank/implementation/request-reply-tracing/
└── handlers-integration-plan.md

tests/integration/handlers/
├── utils.py
├── test_allocate_resources.py
├── test_integrate_maps.py
├── test_perform_exploration.py
├── test_plan_route.py
└── test_release_resources.py
```
