# Product Context

## Why This Project Exists

- To demonstrate and evaluate the Saga pattern for distributed consistency in a robotics SLAM workflow.
- To avoid global ACID transactions by using explicit compensating actions for rollback.

## Problems It Solves

- Maintains data consistency across multiple service steps without distributed transactions.
- Provides a clear rollback mechanism for partial failures in multi-step robot exploration.

## How It Should Work

- Orchestrates a sequence of robot SLAM tasks using Celery, with compensating tasks for each step.
- Uses Docker Compose for easy deployment and management of all services.
- Provides real-time monitoring and debugging via Flower UI.

## User Experience Goals

- Simple, scriptable setup and operation.
- Clear visibility into each step and compensation in the workflow.
- Easy to observe, test, and debug Saga flows.
