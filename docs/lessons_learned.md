# Lessons Learned and Implementation Playbook

This proof-of-concept validated that Celery, Redis Streams, and async command handlers can orchestrate a compensating saga for collaborative SLAM missions. The steps below capture the repeatable approach and key insights needed to reproduce the architecture in another domain.

## 1. Frame the Workflow as a Saga

1. Identify mission phases and matching compensations; represent each step as a Celery task or async function.
2. Build a chain with explicit `link_error` callbacks so compensations fire automatically when downstream tasks fail. 【F:app/flows/mission_start_celery/orchestrator.py†L32-L50】
3. Generate saga-scoped correlation IDs to trace every command and reply. 【F:app/flows/mission_start_celery/orchestrator.py†L23-L31】

**Insight:** Treat compensations as first-class Celery tasks. This keeps orchestration declarative and makes failure handling observable through Flower.

## 2. Decouple Work through Redis Streams

1. Publish commands with `request_and_reply` so Celery tasks and async handlers communicate via Redis Streams. 【F:app/flows/mission_start_celery/tasks.py†L18-L78】
2. Use consumer groups per handler to enable horizontal scaling without duplicate processing. 【F:app/commands/listener.py†L64-L92】
3. Embrace timeouts in the request/reply helper to guard against hung handlers. 【F:app/flows/mission_start_celery/tasks.py†L22-L30】

**Insight:** Redis Streams give durable back-pressure and replay semantics, which simplified our recovery strategy compared to transient queues.

## 3. Standardize Handler Telemetry

1. Wrap every handler with `multi_stage_reply` to emit start, progress, completed, and failed events. 【F:app/redis_utils/decorators.py†L9-L58】
2. Pass the reply stream name through command payloads so handlers can push status updates to the correct channel. 【F:app/flows/mission_start_celery/tasks.py†L20-L72】
3. Surface fractional progress to unlock richer mission dashboards and automated retries.

**Insight:** A uniform decorator drastically reduced boilerplate and made monitoring symmetrical across services.

## 4. Keep the Listener Lightweight and Idempotent

1. Discover handler modules dynamically to eliminate manual registration drift. 【F:app/commands/listener.py†L18-L39】
2. Create consumer groups on startup but tolerate BUSYGROUP errors so restarts stay idempotent. 【F:app/commands/listener.py†L70-L87】
3. Acknowledge messages only after handlers succeed; log failures to aid replay.

**Insight:** The listener forms the boundary between Celery orchestration and async services. Keeping it stateless lets us scale more listeners when mission load grows.

## 5. Provide Alternate Execution Paths for Testing

1. Mirror the Celery saga with a pure-async orchestrator to run deterministic tests without workers. 【F:app/flows/mission_start_async/orchestrator.py†L1-L96】
2. Reuse the same `request_and_reply` contract so both backends exercise identical handlers. 【F:app/flows/mission_start_async/orchestrator.py†L40-L80】
3. Trigger the desired backend through the `mission:start` handler's `backend` parameter for scenario coverage. 【F:app/commands/handlers/start_mission.py†L24-L47】

**Insight:** Offering a Celery and pure-async path de-risks orchestration changes by enabling test suites that avoid worker scheduling variability.

## 6. Containerize the Runtime Early

1. Compose Redis, PostgreSQL, Celery workers, Flower, and the listener in Docker Compose to codify infrastructure. 【F:docker-compose.yml†L1-L74】
2. Gate service startup on health checks to guarantee Redis is ready before Celery workers boot. 【F:docker-compose.yml†L23-L34】
3. Mount the application directory for rapid inner-loop iteration while retaining container parity.

**Insight:** The Compose stack doubles as both development and integration-test environment, ensuring parity and shortening feedback loops.

## 7. Make Observability a First-Class Concern

1. Enable Celery event tracking (`-E`) so Flower captures task lifecycle events. 【F:docker-compose.yml†L23-L34】
2. Emit structured telemetry via Redis replies for mission dashboards and audit trails. 【F:app/redis_utils/decorators.py†L24-L55】
3. Log correlation IDs at every layer to map saga progress across systems. 【F:app/flows/mission_start_celery/orchestrator.py†L23-L31】

**Insight:** Observability requirements shape the contract between orchestrator, tasks, and handlers; designing telemetry up front prevents opaque failure modes.

## 8. Testing Checklist

- Run the async orchestrator in isolation to validate handler logic deterministically. 【F:app/flows/mission_start_async/orchestrator.py†L1-L96】
- Execute Celery-based sagas inside Docker Compose and inspect Flower for task flow regressions. 【F:docker-compose.yml†L23-L34】
- Add integration tests that push commands onto Redis Streams and assert replies to cover the end-to-end contract. 【F:tests/integration/test_orchestrator_trigger.py†L1-L88】

**Insight:** A layered testing strategy (async unit tests + Celery integration tests) keeps the saga reproducible and debuggable.

