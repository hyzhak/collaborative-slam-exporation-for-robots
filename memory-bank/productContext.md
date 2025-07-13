# Product Context

## Why This Project Exists

- To demonstrate and evaluate the Saga pattern for distributed consistency in a robotics SLAM workflow.
- To avoid global ACID transactions by using explicit compensating actions for rollback.

## Problems It Solves

- Maintains data consistency across multiple service steps without distributed transactions.
- Provides a clear rollback mechanism for partial failures in multi-step robot exploration.

## How It Should Work

- Orchestrates a sequence of robot SLAM tasks using Celery, with compensating tasks for each step.
- Uses Redis Streams for event-driven orchestration and command/event propagation.
- Each orchestration is tracked by a unique `saga_id` and a persistent `correlation_id` that is required and propagated through all events and commands.
- All event/command emission uses only top-level fields: `correlation_id`, `saga_id`, `event_type`, `status` (for events), `payload`, and `timestamp`.
- The `domain` field has been removed from all event/command emissions and function signatures for simplicity.
- Uses Docker Compose for easy deployment and management of all services.
- Provides real-time monitoring and debugging via Flower UI and RedisInsight.

## User Experience Goals

- Simple, scriptable setup and operation.
- Clear visibility into each step and compensation in the workflow.
- Easy to observe, test, and debug Saga flows.
