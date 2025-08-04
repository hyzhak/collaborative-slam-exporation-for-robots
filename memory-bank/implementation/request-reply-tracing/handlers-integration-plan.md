# Handler Integration Tests Design

**Status:** All handler integration tests exist and pass as designed.

- Each handler emits “start → progress → completed” as required.
- Stream names and groups align with plan.
- Integration tests in tests/integration/handlers/ confirm correct sequence and metadata.

## 1. Purpose

Define end-to-end integration tests that verify each command handler listens on its Redis stream and emits a “start → progress → completed” sequence against a live Redis service.

## 2. Infrastructure

- Docker Compose environment (uses `redis://redis:6379/0`).
- Tests run as a separate service under `docker-compose.integration.yaml`.
- Reuses existing Redis and orchestrator listener service.

## 3. Test Scope

**Status:** Confirmed.

- One test module per handler exists.
- Focus is on multi-stage replies; business logic is not tested.

- One test module per handler (allocate, integrate, perform, plan, release).
- Focus on multi-stage replies only; business logic verification (e.g., sleep) is out of scope.

## 4. Shared Utilities (`tests/integration/handlers/utils.py`)

**Status:** Confirmed.

- Utilities implemented and used in all handler integration tests.

- `redis_client` fixture (synchronous `redis.Redis`).
- `send_command(stream, event_type, correlation_id, saga_id, extra_fields=None)`: XADD command stream.
- `collect_events(stream, group, correlation_id, expected_statuses, timeout)`: XREADGROUP loop collecting statuses.

## 5. Stream & Handler Matrix

**Status:** Confirmed.

- Stream names, groups, and event types match implementation.

| Handler             | Stream               | Group                     | Event Type          |
| ------------------- | -------------------- | ------------------------- | ------------------- |
| allocate_resources  | resources:commands   | resources_handler_group   | resources:allocate  |
| integrate_maps      | map:commands         | map_handler_group         | map:integrate       |
| perform_exploration | exploration:commands | exploration_handler_group | exploration:perform |
| plan_route          | routing:commands     | routing_handler_group     | routing:plan        |
| release_resources   | resources:commands   | resources_handler_group   | resources:release   |

## 6. Test Flow (per module)

**Status:** Confirmed.

- Integration tests use dedicated consumer groups and unique IDs.
- Sequence and assertions match plan.

1. Create a dedicated consumer group for reply stream (e.g., `<stream>:integration_test_group`) to avoid interference with groups used by the orchestrator or listeners.
2. Generate unique `correlation_id`, `saga_id`.
3. Call `send_command(...)`.
4. Call `collect_events(...)` expecting `["start","progress","completed"]` using the dedicated group.
5. Assert correct order and payload fields (fraction increases, matching IDs).

## 7. Assertions

**Status:** Confirmed.

- All assertions implemented in integration tests.

- First status == “start”
- At least one progress with `fraction` > 0 and ≤ 1
- Final status == “completed”

## 8. File Structure

**Status:** Confirmed.

- File structure matches implementation.

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
