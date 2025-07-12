## Brief overview

- Guidelines for manually validating Saga orchestration and compensation logic using Celery, Flower, and containerized infrastructure.
- Project-specific rules for triggering, observing, and troubleshooting orchestration runs.

## Manual orchestration triggering

- Always trigger the orchestrator from within the Celery worker container to ensure correct import paths and environment.
- Use the following command pattern:

  ```bash
  podman-compose exec celery_worker python -m app.orchestrator 2 ZoneA
  ```

- Adjust arguments as needed for robot count, area, or failure simulation.

## Validation workflow

- Monitor task execution and compensation in real time using the Flower UI at <http://localhost:5555>.
- Confirm that all Saga steps and compensating tasks appear in the correct sequence.
- Use logs from the orchestrator and worker containers for additional traceability.

## Documentation and reproducibility

- Document manual validation steps and troubleshooting tips in the README for future reference.
- Prefer explicit, copy-pasteable commands for orchestration and validation.
