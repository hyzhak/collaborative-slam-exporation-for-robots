# Collaborative SLAM Exploration for Robots

A proof-of-concept implementation of the Saga pattern for orchestrating multi-step, distributed workflows using Celery, Redis, PostgreSQL, and Flower. The scenario simulates collaborative SLAM (Simultaneous Localization and Mapping) exploration by multiple robots, with robust rollback (compensation) logic for failures.

## Key Features

- **Saga Pattern Orchestration:** Implements the Saga pattern using Celery to coordinate a sequence of tasks and compensations.
- **Celery Task Queue:** Asynchronous task execution and orchestration.
- **Redis Broker & Backend:** Fast in-memory message broker and result backend for Celery.
- **PostgreSQL Database:** Shared persistent state for simulating service data.
- **Flower Monitoring UI:** Real-time visualization and debugging of task flows.
- **Docker Compose Infrastructure:** All components run as containers for easy setup and teardown.
- **Optional FastAPI Trigger:** HTTP endpoint for starting Sagas (optional).

## Architecture Overview

- **Celery Worker:** Runs all Saga step and compensation tasks.
- **Saga Orchestrator:** Coordinates task execution and compensation on failure.
- **Redis:** Message broker and result backend for Celery.
- **PostgreSQL:** Shared database for simulating persistent state.
- **Flower:** Web UI for monitoring Celery tasks.
- **(Optional) FastAPI:** HTTP API to trigger Saga runs.

All services are defined in `docker-compose.yml` and run together on a single machine.

## Prerequisites

- Docker & Docker Compose (or Podman Compose)
- Python 3.11+ (for local development/testing)
- (Optional) Make sure ports 5432 (Postgres), 6379 (Redis), 5555 (Flower), and 8000 (API) are available.

## Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/hyzhak/collaborative-slam-exporation-for-robots.git
   cd collaborative-slam-exporation-for-robots
   ```

2. **Build and start all services:**

   ```bash
   docker-compose up --build -d
   ```

3. **Check that all containers are running:**

   ```bash
   docker-compose ps
   ```

4. **(Optional) Initialize the database:**  
   If your tasks require tables, create them in the Postgres container.

5. **Trigger a Saga run:**
   - **Via container (recommended):**

     ```bash
     podman-compose exec celery_worker python -m app.orchestrator 2 ZoneA
     ```

     - Adjust arguments as needed for robot count, area, or failure simulation.

   - **Via API (if enabled):**  
     Send a POST request to `/start_saga` on port 8000.

6. **Monitor progress:**  
   Open [http://localhost:5555](http://localhost:5555) to view the Flower UI.

## Project Structure

```
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── celery_app.py      # Celery app configuration
│   ├── tasks.py           # Saga step & compensation tasks
│   ├── orchestrator.py    # Saga orchestration logic
│   └── api.py             # (Optional) FastAPI app
├── memory-bank/           # Project documentation & context
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
```

## Testing the Saga

- Run the orchestrator to start a Saga.
- Simulate failures (by parameters or randomization in tasks) to observe compensation logic.
- Use Flower UI and logs to trace task execution and rollback steps.
- Inspect the PostgreSQL database to verify state changes and rollbacks.

## Contributing

Contributions are welcome! Please follow the Conventional Commits specification for commit messages.

## License

This project is licensed under the MIT License.
