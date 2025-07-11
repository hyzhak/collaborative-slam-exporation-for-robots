# System Patterns

## System Architecture

- Orchestration-based Saga pattern with a central orchestrator.
- Components:
  - Celery workers (host Saga steps and compensations as tasks)
  - Saga orchestrator (coordinates task execution and compensation)
  - Redis broker (Celery message/event stream)
  - PostgreSQL database (shared state for tasks)
  - Flower UI (real-time monitoring)
  - (Optional) FastAPI for HTTP-triggered orchestration

## Key Technical Decisions

- Use Docker Compose to containerize and manage all services.
- Use Redis as both broker and result backend for Celery.
- Use a single Postgres instance for all tasks (simulating service-local state).
- All communication between components via Docker network.

## Design Patterns in Use

- Saga orchestration (centralized control, explicit compensation)
- Task-based microservice simulation (each Celery task = service action)
- Compensation pattern for rollback

## Component Relationships

- Orchestrator triggers tasks on Celery workers via Redis.
- Workers update/query Postgres as needed for state.
- Flower UI connects to Redis to visualize task flow and status.
- All components interact within a single Docker Compose network.

## Critical Implementation Paths

- Sequential execution of Saga steps with error handling.
- On failure, orchestrator triggers compensating tasks in reverse order.
- Logging and saga_id propagation for traceability.
