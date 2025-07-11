# Collaborative SLAM Exploration Saga PoC

## Core Requirements and Goals

- Implement a proof-of-concept for the Saga pattern using Celery as the orchestrator.
- Demonstrate orchestration of multi-step robot SLAM (Simultaneous Localization and Mapping) exploration tasks.
- Use Docker Compose to manage all services: Celery workers, Redis broker, PostgreSQL, and Flower UI.
- Ensure data consistency across distributed steps without distributed transactions, using compensating tasks for rollback.
- Provide real-time visibility and debugging of Saga flows via Flower UI.
- All components must be open-source and run on a single Ubuntu server.
- The scenario: multiple robots coordinate to explore and map an environment, with each step and compensation modeled as a Celery task.
- Evaluate Celery and Flower for suitability as a Saga orchestration and monitoring platform.
