# Celery Saga Pattern Proof-of-Concept Setup Guide

## Overview of the Saga Pattern and Approach

**Saga Pattern:** The Saga design pattern is a way to maintain data consistency across multiple services without using distributed transactions. A *saga* is essentially a sequence of operations (transactions) that each execute in a single service, with compensating operations to undo them if something fails. In simpler terms, if one step in a multi-step process fails, the Saga will invoke **compensating transactions** to roll back the previous steps, rather than locking resources or using a global commit/rollback. This avoids ACID transactions across services, at the cost of having to explicitly define the rollback logic.

**Orchestration vs. Choreography:** Sagas can be coordinated in two ways. In **orchestration**, a central Saga orchestrator tells each service what action to perform next (and what compensations to run on failures). In **choreography**, there is no central coordinator – services emit and listen to events to decide the next action. For this proof-of-concept, we will use the **orchestration approach**: a single orchestrator will sequence the tasks and trigger compensations if needed.

**Our Goal:** We will implement a Saga pattern PoC using **Celery**, a Python asynchronous task queue, to orchestrate a series of tasks (simulating services) and their compensations. We want to evaluate how Celery performs as a Saga orchestration platform – whether it provides the needed visibility (with the help of Flower UI) and ease of debugging for Saga flows. The scenario we’ll use is a **Collaborative SLAM (Simultaneous Localization and Mapping) Exploration for Robots**: multiple robots coordinating to explore an environment and build a map. This domain is just an example to make the tasks concrete. We’ll create a few simple “services” (Celery tasks) such as allocating robots, planning routes, performing exploration, and integrating maps. These will be strung together into a Saga, complete with compensating tasks (e.g. deallocate robots, abort exploration) to undo steps on failure.

**Key Requirements:** All components will run on a single Ubuntu server using Docker containers (managed via **docker-compose**). We will use all free/open-source images. The **message broker** for Celery will be Redis (specifically leveraging Redis’s fast in-memory queueing – effectively using Redis as a “stream” of events/tasks). We will include a shared **PostgreSQL database** to simulate persistent state for services (if needed by our tasks). We will also use **Flower**, a web-based Celery monitoring tool, to visualize the Saga’s execution in real time. The entire implementation will be in Python (for Celery tasks and any orchestration code), and we aim to keep it lightweight and simple.

## Architecture and Components

Before diving into setup steps, let’s outline the high-level architecture of our Saga PoC system and the Dockerized components:

* **Celery Workers (Saga Services):** We will have one (or multiple) Celery worker processes running our Python code. These workers will host the Saga’s *steps* as Celery tasks (each task representing a service action, e.g. “allocate robot”, “explore area”, “integrate map”). They will also host *compensation tasks* to undo those actions if necessary. Celery allows us to execute tasks asynchronously and to chain or coordinate them in a workflow.

* **Saga Orchestrator:** The Saga orchestration logic can be implemented as a simple Python function or script that coordinates the tasks. The orchestrator will send tasks to Celery in sequence and handle failures by invoking compensation tasks. (Alternatively, one could make the orchestrator itself a Celery task, but for clarity we might run it as a standalone process or via an API call.) The orchestrator embodies the Saga’s control flow: it tells each step to execute and knows which compensating steps to run on failure.

* **Redis Broker (Event Stream):** Celery requires a message broker to send tasks and receive results. We will use **Redis** as the broker (and result backend) for this PoC. Redis is an in-memory data store that Celery can use as a message queue, making it simple and efficient for managing task messages. In our setup, Redis will act as the **event broker**, effectively handling the “task stream” of the Saga. (Celery’s Redis support uses Redis’s messaging lists under the hood to queue tasks, fulfilling the requirement of using a Redis stream for events.)

* **PostgreSQL Database:** We will run a Postgres container that all services share. In a real microservice Saga, each service would have its own database, but for this single-machine demo we’ll use one database (with different tables or schemas per “service” if needed). The Saga tasks can use this database to simulate state changes – for example, a task might insert a row to record “Robot reserved” or update a status. This helps simulate a realistic Saga where each step involves a local transaction on a database. All tasks will use the same Postgres for simplicity (username, password, and DB name will be configured via environment variables in the compose file).

* **Flower Monitoring UI:** **Flower** is an open-source web application for monitoring and administrating Celery clusters. We will include Flower as a container so we have a real-time view of the Saga’s progress. Flower will connect to the Redis broker to gather task events and will provide a dashboard in the browser to see each task’s status, start time, runtime, results, and any exceptions. This is crucial for visualizing the Saga and debugging issues, since we want to assess if Celery+Flower provides sufficient insight into what’s happening in the Saga.

* **FastAPI (Optional):** The use of FastAPI is optional. We could include a small FastAPI app to trigger the Saga via an HTTP request for convenience (for example, an endpoint `/start_saga` that kicks off the orchestrator). However, since this is a PoC and can be script-based, it’s not strictly necessary. We may simply run the orchestrator function manually (or via a one-off container) to start the Saga. If ease of testing via web is desired, FastAPI could be added to accept a request and then call the saga orchestration logic in the background.

**Inter-component Interaction:** The workflow in operation will look like this (using orchestration pattern):

1. **Saga Start:** We initiate the Saga (either by running a script or hitting an API endpoint). The orchestrator (running on the Python app container) begins the Saga by sending the first task to Celery.

2. **Task Execution:** The Celery worker receives the task from Redis, executes it (e.g., “allocate\_resources”), and returns a result (or error). The result is stored in Redis (as we configured Redis also as the result backend) so the orchestrator can check the outcome.

3. **Sequential Steps:** The orchestrator then sends the next task (e.g., “perform\_exploration”) with necessary data (perhaps the output of the previous step or a common Saga ID). Each task runs in order. If all goes well, the Saga proceeds through all steps to completion (e.g., finishing with “integrate\_results”).

4. **Failure and Compensation:** If any task fails (throws an exception), Celery will mark it as failed and return an error status. The orchestrator detects this and will **trigger compensating tasks** for all previously completed steps in reverse order. For example, if the exploration step fails after allocation succeeded, the orchestrator will call a “abort\_exploration” (if needed) and then “deallocate\_resources” task to undo the partial work. Each compensation is itself a Celery task executed by the workers. After compensation, the Saga is considered rolled back/aborted.

5. **Monitoring:** Throughout this process, Flower is collecting events. We can refresh the Flower UI to see each task (forward steps and compensations) appear with their status (PENDING, STARTED, SUCCESS, or FAILURE). This gives us a visual timeline of what happened in the Saga. Flower can list tasks by name and ID, show their arguments, results, and any error tracebacks, which is invaluable for debugging Saga logic.

## Step 1: Setting Up Docker Compose Infrastructure

To containerize the Saga PoC, we’ll use **Docker Compose** to define all the required services. We assume you have a project repository with a main directory ready. Inside this directory, create a **`docker-compose.yml`** file and include the following services:

1. **Redis Service:** Add a service for the Redis broker. Use the official Redis image (e.g., `redis:7-alpine` for a lightweight image). No special configuration is needed for basic usage. For example:

   ```yaml
   services:
     redis:
       image: "redis:7-alpine"
       container_name: saga_redis
       ports:
         - "6379:6379"
       # (Using the default Redis port 6379, exposed to host for debugging if needed)
   ```

   This will launch a Redis server that Celery will use as the message broker (and we will also use it for result backend). Redis is an in-memory store and works well as a fast broker for Celery. We don’t need to persist data for this PoC, so running Redis without volumes is fine (if the container restarts, losing broker state is acceptable in development).

2. **PostgreSQL Service:** Add a Postgres service to the compose. Use the official Postgres image (e.g., `postgres:15-alpine`). Set environment variables for `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` to initialize the database at startup. For example:

   ```yaml
     db:
       image: "postgres:15-alpine"
       container_name: saga_postgres
       environment:
         - POSTGRES_DB=sagadb
         - POSTGRES_USER=sagauser
         - POSTGRES_PASSWORD=sagapass
       ports:
         - "5432:5432"
       volumes:
         - pgdata:/var/lib/postgresql/data
   volumes:
     pgdata:
   ```

   This will create a database named `sagadb` with user `sagauser` (password `sagapass`). We expose port 5432 to host (optional) and mount a volume for persistent storage of data (so the DB retains state if containers restart). All Saga tasks/services will connect to this same database (using these credentials) for any data they need to store. Sharing one DB is a simplification for this demo, but it mimics multiple services updating a common state. (In production, they might have separate DBs, but the Saga orchestrator would still ensure consistency by compensation). The docker-compose commentary confirms that lines defining the Postgres service include the env vars to initialize it and that the data is stored in a volume.

3. **Celery Worker Service:** This is the core application container that will run our Celery workers (and possibly the orchestrator code). We will build this image from our own code, so specify a build context. For example:

   ```yaml
     celery_worker:
       build: .
       container_name: saga_worker
       depends_on:
         - redis
         - db
       environment:
         - CELERY_BROKER_URL=redis://redis:6379/0
         - CELERY_RESULT_BACKEND=redis://redis:6379/0
         - POSTGRES_HOST=db
         - POSTGRES_DB=sagadb
         - POSTGRES_USER=sagauser
         - POSTGRES_PASSWORD=sagapass
       command: celery -A app.celery_app worker --loglevel=info
   ```

   In this snippet, we assume:

   * The Dockerfile in the current directory builds our app (more on that in Step 2).
   * We name the Celery application `app.celery_app` (this refers to a Celery instance created in our code). The `command` starts a Celery worker for that app with INFO log level.
   * `depends_on` ensures Redis and Postgres start before the worker.
   * We pass environment variables for Celery broker and backend URLs pointing to the Redis service (using the Redis container’s hostname on the Docker network). Here we use database index `0` on Redis (the `redis://redis:6379/0` URL) for both broker and result backend. This means Celery will send task messages to Redis and also store task states/results in Redis (allowing orchestrator or Flower to query task outcomes).
   * We also pass Postgres connection info as environment variables. Our code can read these (or we could bake them into settings) to connect to the database. For example, `POSTGRES_HOST=db` tells the app that the DB hostname is “db” (the service name on the Docker network), and the credentials match what we set above.
   * (Optional) We could scale out multiple Celery workers if desired (e.g., `deploy: replicas: 2` in a Swarm or using `docker-compose up --scale` for testing). But for the PoC one worker process is enough.

4. **Flower Service:** Add a service for Flower, the Celery monitoring UI. We can use the `mher/flower` Docker image which is a lightweight way to run Flower. For example:

   ```yaml
     flower:
       image: "mher/flower:latest"
       container_name: saga_flower
       depends_on:
         - redis
       ports:
         - "5555:5555"
       command: flower --broker=redis://redis:6379/0 --port=5555
   ```

   This will launch Flower on port 5555 (accessible via `http://<server-ip>:5555`). We point Flower at the same Redis broker used by Celery. Flower will then listen to task events from Redis and present them on its web UI. We depend on Redis to be up (Flower doesn’t need direct DB or Celery worker access; it just reads task events from the broker and backend). With this, once everything is running, you can open Flower in a browser to monitor the saga’s execution in real time.

5. **(Optional) API Service:** If you choose to have a FastAPI (or Flask) app to trigger the Saga via HTTP, you can add another service, e.g., `api`, that runs the FastAPI app. This service would also use the same code image (or a similar one) and could depend on the worker (or not, since both use the same code base). For example:

   ```yaml
     api:
       build: .
       container_name: saga_api
       depends_on:
         - redis
         - db
       environment:
         # similar env for DB and broker as worker
       command: uvicorn app.api:app --host 0.0.0.0 --port 8000
       ports:
         - "8000:8000"
   ```

   This would run a FastAPI app (if our code includes one) on port 8000. The FastAPI app might have an endpoint like `POST /start_saga` that internally invokes the saga orchestration (perhaps by calling a Celery task or direct function). However, **if you don’t need an HTTP interface**, you can skip this and just run the saga by executing a script. We will proceed assuming a script/manual trigger for simplicity.

Once you have defined these services in `docker-compose.yml`, you can verify the file structure. At minimum, your project directory now contains:

* `docker-compose.yml`
* (plus you will add code files like Dockerfile, tasks code, etc., in subsequent steps).

Ensure that Docker is installed and running on your remote Ubuntu server. You might also want to create a Python virtual environment locally for development (if not editing directly on server) to manage dependencies, but since we’ll use Docker for running, it’s optional for the PoC.

## Step 2: Building the Application Container (Dockerfile and Requirements)

Next, prepare the environment for the Celery application (the Saga code). We need to containerize our Python code with all necessary dependencies:

1. **Write a Requirements File:** Create a `requirements.txt` (or `pyproject.toml` if using Poetry, but requirements.txt is straightforward) listing the Python packages we will use. At minimum, include:

   * `celery` (Celery library for tasks).
   * `redis` or `celery[redis]` (Celery’s Redis support, although installing just `celery` usually covers it, specifying `celery[redis]` ensures Kombu (the messaging library) has Redis drivers).
   * `flower` (for completeness, though we run Flower in a separate container, we might not need to install it in our app container; only install if we plan to possibly run Flower from code or use any of its features in app).
   * `fastapi` and `uvicorn` if you plan to use a FastAPI server for triggers.
   * `psycopg2-binary` or `asyncpg` (for Postgres access, depending on if you use synchronous or async DB access; psycopg2 is the standard for sync).
   * Optionally `SQLAlchemy` if you want an ORM to interact with Postgres in tasks.
   * Any other utility libraries you might use (e.g., for logging or config).

   An example `requirements.txt` might look like:

   ```
   celery==5.2.7
   redis==4.5.5
   flower==1.1.0
   fastapi==0.95.2  # if using FastAPI
   uvicorn==0.22.0  # if using FastAPI for running server
   psycopg2-binary==2.9.6
   SQLAlchemy==1.4.47   # optional, for DB modeling
   ```

   Pin versions as needed. Ensure these are all free/open source. (Celery, Flower, FastAPI, etc., are all open source).

2. **Write a Dockerfile:** In the project directory, create a file named **`Dockerfile`** to build the Celery worker (and app) image. For example:

   ```dockerfile
   FROM python:3.11-slim

   # Set work directory
   WORKDIR /app

   # Install system deps (if any needed, e.g., for psycopg2 compile, but psycopg2-binary should include them)
   # RUN apt-get update && apt-get install -y libpq-dev build-essential

   # Copy requirements and install
   COPY requirements.txt ./
   RUN pip install -r requirements.txt

   # Copy application code
   COPY . /app

   # Set environment (if not using docker-compose env, you can set defaults here)
   ENV CELERY_BROKER_URL=redis://redis:6379/0 \
       CELERY_RESULT_BACKEND=redis://redis:6379/0

   # (We won't define CMD here, as docker-compose will override the command for the worker and API)
   ```

   This Dockerfile uses a slim Python base image, installs our Python dependencies, then copies in our code. It also sets environment variables for Celery broker and backend by default (the compose file also provides them, so this is optional redundancy). Note: If using an Alpine-based Python image, be mindful of installing dependencies like gcc or libpq for psycopg2; using the slim Debian image often avoids those headaches for psycopg2.

   Make sure your code files (which we will create in the next steps) are in the build context (the current directory). That includes the Celery app and tasks, and any orchestrator script or FastAPI app.

3. **Project Structure:** Organize your project files. For instance, you could have a structure:

   ```
   project/
   ├── docker-compose.yml
   ├── Dockerfile
   ├── requirements.txt
   └── app/
       ├── __init__.py
       ├── celery_app.py     # Celery application configuration
       ├── tasks.py          # Saga task definitions
       ├── orchestrator.py   # Saga orchestration logic (if separate)
       └── api.py            # FastAPI app (if using FastAPI)
   ```

   The exact structure can vary, but ensure that the Celery app and tasks are in a Python module that the worker can import. Here we use `app/` as a module (so `app.celery_app` will be the Celery instance path).

4. **Build the Image:** Once the Dockerfile and compose are ready, you can build the Docker image for our app. Run:

   ```bash
   docker-compose build
   ```

   This will install all dependencies and prepare the image. You should see output for pip installing Celery, etc. If there are errors, adjust the Dockerfile accordingly (e.g., installing missing system libs). After a successful build, Docker will have an image (likely named something like `project_celery_worker:latest` if no explicit names given).

With the infrastructure in place and image built, we can proceed to coding the Celery application and Saga logic.

## Step 3: Configuring Celery and Defining the Task Workflow

In this step, we set up the Celery application and define the Saga tasks. We won’t write the full code here, but outline what needs to be done in each part:

1. **Celery Application Setup (app/celery\_app.py):** Create a Celery instance and configure it to use Redis. For example:

   ```python
   from celery import Celery

   # Broker and backend URLs can come from env variables for flexibility
   broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
   backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

   celery_app = Celery("saga_app", broker=broker_url, backend=backend_url)
   celery_app.conf.update({
       "task_track_started": True,     # enables tracking STARTED state
       "result_extended": True,        # store extended result (traceback) on failure
       # ... any other Celery config as needed
   })
   ```

   This creates a Celery application named `"saga_app"` using Redis as the message broker and result backend. Using Redis for both means the Celery workers will both get tasks from Redis and store task state there. We enabled `task_track_started` so that tasks report a "STARTED" state (visible in Flower) when they begin execution, and `result_extended` to keep error tracebacks. You might also configure task routes or serializer if needed, but not necessary for a simple PoC.

   Importantly, make sure this Celery instance is loaded when the worker starts. Our docker-compose command `celery -A app.celery_app worker...` will import `app/celery_app.py`, instantiate the Celery app, and auto-discover tasks. Celery by default will autodiscover tasks in modules listed in `celery_app.autodiscover_tasks([...])` or you can manually import tasks module in this file to register the tasks. For simplicity, you can do:

   ```python
   celery_app.autodiscover_tasks(['app'])
   ```

   if your tasks are in `app/tasks.py` decorated with `@celery_app.task`.

2. **Defining Saga Tasks (app/tasks.py):** This file will contain the actual task definitions – both the main Saga steps and their compensations. We will create simple Python functions for each step, then decorate them as Celery tasks. For our Collaborative SLAM example, we can define tasks like:

   * `allocate_resources(saga_id, robot_count)` – Reserve the required robots for the mission. E.g., mark robots as allocated in the database (or simply simulate by printing/logging). **Compensation:** if something fails later, we will need to release these robots.
   * `plan_route(saga_id, area)` – Compute an exploration route for the robots in the given area. This might produce a plan or map. (This step might not need a direct compensation beyond what releasing robots covers, but if it created a plan record in DB, a compensation could delete that plan.)
   * `perform_exploration(saga_id, robot_id_list)` – Command the robots to perform the exploration according to the plan. This could simulate the process (perhaps by sleeping a few seconds or random success/failure). **Compensation:** if exploration fails halfway, we might issue an abort command to any robot still active.
   * `integrate_maps(saga_id)` – Take the data from all robots and integrate into a final map. This is the final step that yields the combined SLAM result. **Compensation:** if integration fails, perhaps discard any partial integrated data (and ensure any robots still logging data are stopped – though in this sequence, by the time we integrate, exploration is done).

   And for each of these forward tasks, define a corresponding compensation task:

   * `release_resources(saga_id)` – If called, undo `allocate_resources` by freeing up the robot reservations (e.g., update DB to mark them available).
   * `abort_exploration(saga_id)` – If called, instruct any ongoing exploration to stop. (In our simple sim, maybe just log that we aborted.)
   * `rollback_integration(saga_id)` – If called, undo any partial results from integration (maybe delete a partially written map record, etc.).

   When writing these tasks:

   * Use the `@celery_app.task` decorator to register them as Celery tasks. You can give them explicit names if you want (especially if simulating separate services, you might prefix with service name, e.g., `@celery_app.task(name="robot_service.allocate")`).
   * Accept a `saga_id` (an identifier for the saga execution) as a parameter to each task. This is useful for logging and debugging – all tasks with the same saga\_id belong to one Saga flow. The orchestrator will generate or use a unique saga\_id for each run and pass it to all tasks. This way, in logs or Flower UI, you can correlate tasks by saga\_id. For example, in Flower you can click on a task and see its arguments (saga\_id will be there).
   * Simulate work: for example, a task can `time.sleep(2)` to mimic a process, or print log statements (which will appear in the worker’s logs). If using Postgres, you can connect (using psycopg2 or SQLAlchemy) and do simple inserts/updates to simulate a state change (like `INSERT INTO robots(status) VALUES ('allocated')` or update a “missions” table, etc.). Keep it lightweight – the goal is just to have some observable action.
   * Introduce controlled failure for testing: To see Saga compensation in action, you may want certain tasks to sometimes fail. You can implement this in a few ways:

     * Accept a parameter like `fail=False`, and if set True, the task raises an Exception to simulate a failure at that step.
     * Or use randomness: e.g., `if random.random() < 0.3: raise Exception("Simulated failure")`. This will make the Saga occasionally hit a failure in a step, allowing you to test the rollback logic.
     * Or determine failure by saga\_id or input (not recommended for real, but for predictable testing you could say if saga\_id ends in certain digit, fail).
   * Log important events: Use Python’s logging or print to note when a task starts, succeeds, or if it’s about to raise an error. These logs will show up in the container logs (`docker-compose logs saga_worker`) and help trace execution alongside Flower. For example:

     ```python
     import logging
     logger = logging.getLogger(__name__)
     @celery_app.task
     def allocate_resources(saga_id, robot_count):
         logger.info(f"Saga[{saga_id}]: Allocating {robot_count} robots")
         # simulate DB update
         # if fail condition:
         #    logger.error(f"Saga[{saga_id}]: Allocation failed!")
         #    raise Exception("Allocation failed")
         logger.info(f"Saga[{saga_id}]: Successfully allocated robots")
         return {"robots_allocated": robot_count}
     ```

     Similar logging should be in compensation tasks, e.g., `"Saga[123]: Releasing robots"` so you can see the order of actions in logs.

   By structuring tasks this way, each one represents a distinct microservice action in the Saga. Celery workers could even be configured to route tasks to different queues to mimic different services (for example, `allocate_resources` and `release_resources` could be in a “RobotService” queue, `plan_route` in a “MappingService” queue, etc.). However, for simplicity, we can run a single worker process that listens to all tasks (default queue) – it’s still logically simulating multiple services.

3. **Compensation Task Behavior:** It’s worth noting how we plan to use these compensation tasks. They will *not* be invoked unless a failure happens. We won’t automatically run all compensations at the end – only as needed to undo a failed saga. (In a real scenario, if the Saga succeeds fully, you might do some finalization like free resources normally as part of the last step. For example, after successful integration, we might call `release_resources` as a normal step to return robots to pool. But in Saga pattern terms, that wouldn’t be a “compensation” but a normal workflow step. In our PoC, we might simplify and only free resources on failure to illustrate compensation, or call it explicitly at end too — either approach is fine as long as we demonstrate compensation on error.)

At this stage, we have Celery tasks ready for both the main saga steps and the rollback steps. Next, we need to implement the Saga orchestrator that ties these tasks together in the correct sequence with error handling.

## Step 4: Implementing the Saga Orchestrator Logic

With tasks defined, the Saga orchestrator is the piece that will coordinate their execution. This can be done in a few ways. We’ll describe a simple approach using a Python function that calls tasks sequentially and handles errors. (Advanced alternatives include using Celery **Canvas** primitives like chains and adding error callbacks (errbacks) to tasks, but handling compensation for multiple steps via Canvas can become complex. For clarity, a straightforward procedural orchestration is easier to follow for a PoC.)

**Approach:** We will write a function (or a Celery task, but likely just a normal function invoked from a script or API) that does the following:

1. Generate a unique `saga_id` (if not provided). This could be a UUID or simply an incrementing number or timestamp. This ID will be used in all tasks as an identifier for this Saga run.

2. Start the first step by sending the Celery task and wait for the result. In Celery, if we call `result = allocate_resources.delay(saga_id, robot_count)`, it returns an AsyncResult. We can then call `result.get()` to wait for it to finish (or we could poll result.state). Since this is a PoC, blocking and waiting is acceptable. (Note: Calling `get()` inside a Celery task is generally not recommended as it can deadlock if not careful. But our orchestrator will be running outside the Celery worker, e.g., as a separate process or thread triggered by the API or script. So it can wait for tasks to complete).

3. Check if the task succeeded or failed:

   * If the result raises an exception (meaning the task failed), catch it and **trigger compensation** for that step if needed. If the failure happened at the first step, there’s nothing to compensate before it – the saga simply fails. If at a later step, call the compensating task(s) for all prior steps.
   * If the result is successful, extract any needed info from it (e.g., `robots_allocated` count or IDs) to pass to the next step.

4. Move to the next task in sequence and repeat the send->wait->check cycle.

5. Continue until all steps complete successfully. If all succeed, the Saga is complete. You might log or return a message indicating success (and possibly trigger any normal completion action, like freeing resources if you chose to do that at end).

6. If a failure occurs at step N, perform rollback:

   * You should call the compensating tasks for steps 1 through N-1 in reverse order. This can be done by simply invoking those Celery tasks. For example, if step2 fails after step1 succeeded, call `release_resources.delay(saga_id)` to undo step1. If step3 fails after steps1 and 2 succeeded, call `abort_exploration.delay(saga_id)` (to undo step2) and then `release_resources.delay(saga_id)` (to undo step1).
   * One important consideration: Do we wait for compensation tasks to complete or fire-and-forget? For the sake of completeness, it’s good to wait for them as well (to know they’ve executed). We can use `get()` on each compensation task’s AsyncResult for confirmation, or at least log that they were triggered.
   * If a compensation task itself fails (unlikely in our simple scenario if they’re idempotent), we should note it – but in a real system, compensations should ideally be simple and robust to avoid further failures.
   * After compensations, mark the Saga as aborted. If using a database, maybe update a saga log status to "FAILED". For PoC, just printing/logging “Saga \[id] rolled back due to error: ...” is fine.

7. End the orchestration. If using an API, return an appropriate response (e.g., Saga success or failure). If using a script, just exit or loop if you want to run multiple sagas.

**Implementing the Orchestrator:** This could reside in a file like `app/orchestrator.py`. If we intend to run it as a standalone script via Docker, we might create an entrypoint in compose just for running one saga. But more practically, we’ll either run it manually or via the FastAPI. For now, consider writing it as a function:

```python
def run_saga(robot_count, area):
    saga_id = str(uuid.uuid4())[:8]  # short unique ID
    try:
        # Step 1: Allocate resources
        res1 = allocate_resources.delay(saga_id, robot_count)
        result1 = res1.get(timeout=10)  # wait up to 10s or so
        # (If failed, an exception will be raised here and jump to except)
        # Step 2: Plan route
        res2 = plan_route.delay(saga_id, area)
        result2 = res2.get(timeout=10)
        # Step 3: Perform exploration
        res3 = perform_exploration.delay(saga_id, result1['robots_allocated'])
        result3 = res3.get(timeout=30)  # maybe longer timeout
        # Step 4: Integrate maps
        res4 = integrate_maps.delay(saga_id)
        result4 = res4.get(timeout=10)
        logger.info(f"Saga[{saga_id}] completed successfully! Final map: {result4}")
        # Optionally, release resources normally at end:
        release_resources.delay(saga_id)
    except Exception as e:
        # If any step fails:
        logger.error(f"Saga[{saga_id}] failed: {e}")
        exc_step = determine_failed_step()  # you might infer which step from context
        # Run compensations depending on where it failed:
        if exc_step == "perform_exploration":
            # exploration failed, undo step 2 (if any side-effects) and step 1
            abort_exploration.delay(saga_id)
            release_resources.delay(saga_id)
        elif exc_step == "integrate_maps":
            # integration failed, undo step 3,2,1
            rollback_integration.delay(saga_id)
            abort_exploration.delay(saga_id)
            release_resources.delay(saga_id)
        elif exc_step == "plan_route":
            # plan route failed, undo step 1
            release_resources.delay(saga_id)
        else:
            # failed at allocation or unknown step, nothing to compensate if allocation failed at start
            pass
        logger.info(f"Saga[{saga_id}] compensating transactions dispatched due to failure.")
```

*(The above is illustrative pseudocode – actual implementation might vary in error handling. One way to get the failed step is to wrap each `.get()` in its own try/except to know exactly which one threw.)*

The orchestrator ensures that we explicitly manage the saga’s control flow and invoke compensations as needed. This manual approach aligns with Saga’s requirement that we handle our own rollback logic (since there’s no automatic rollback like a database transaction). The upside is full control; the downside is verbosity and complexity as the number of steps grows (but our PoC has only a few steps).

**Alternative:** As mentioned, Celery offers a **Canvas** (chord, chain, etc.) that can chain tasks together. For example, one could create a chain: `allocate_resources.s(...).set(link_error=release_resources.s()) | plan_route.s(...).set(link_error=release_resources.s()) | ...` and so on. However, linking an error callback that triggers all prior compensations is not straightforward with pure Celery primitives – you might end up needing a custom error handler that knows what to undo. Another approach is to use Celery chords with a callback that triggers compensations on error. These are advanced patterns and beyond the scope of a simple PoC, but feel free to explore Celery’s documentation on errbacks if interested. For our purposes, the explicit orchestrator function is clearer.

At the end of this step, we have:

* Celery tasks for each saga action and compensation.
* An orchestration function to run the saga steps in order and handle failures.

We are now ready to run the system and test the Saga execution.

## Step 5: Running the Services and Executing a Saga

With everything set up, it’s time to launch the Docker Compose services and run a Saga through the system:

1. **Launch the Docker Compose stack:** From your project directory (where docker-compose.yml is), run:

   ```bash
   docker-compose up -d
   ```

   This starts all containers in the background. The sequence will start Redis, Postgres, the Celery worker, Flower, and (if included) the API service. Use `docker-compose ps` to check that all containers are “Up”. If any exit, use `docker-compose logs <service>` to inspect errors (for example, the worker might crash if Celery app import failed or dependencies missing).

2. **Initialize Database (if needed):** If your tasks expect certain tables in Postgres, you should initialize them. For a PoC, you can skip complex DB migrations – a quick way is to exec into the Postgres or worker and create tables manually. For instance:

   ```bash
   docker-compose exec db psql -U sagauser -d sagadb -c "CREATE TABLE robot_allocations(saga_id VARCHAR(50), robot_count INT, allocated_at TIMESTAMP);" 
   ```

   Similarly create any other tables you want (missions, maps, etc.). This is optional – if tasks just do inserts without pre-created tables, they will error. Alternatively, modify tasks to create tables on the fly or use an ORM with `create_all()` on startup. Keep things simple; the focus is Saga flow, not DB schema.

3. **Trigger the Saga Orchestrator:** Now we run the Saga itself. Depending on how you set it up:

   * **If using FastAPI**: Make a request to the endpoint that starts the saga. For example, if you implemented `POST /start_saga` that calls `run_saga(...)`, you’d do:

     ```bash
     curl -X POST http://<server-ip>:8000/start_saga -H "Content-Type: application/json" -d '{"robot_count": 2, "area": "ZoneA"}'
     ```

     The API should respond immediately (if orchestrator is async) or after saga completion (if it waits). In our design, we might have made `run_saga` synchronous. It may be better in an API context to kick off the saga in a background thread or as a Celery task itself and return a saga\_id to poll later. But for PoC, blocking is okay.
   * **If using a script/manual:** You can exec into the worker container and run the orchestrator function. For example:

     ```bash
     docker-compose exec celery_worker python -c "from app import orchestrator; orchestrator.run_saga(2, 'ZoneA')"
     ```

     This will start the saga with 2 robots in area "ZoneA". (Alternatively, you could have a small `if __name__=='__main__':` in orchestrator.py to parse args and run, then you’d do `docker-compose exec celery_worker python app/orchestrator.py --robots 2 --area ZoneA`.)
   * **If using a one-off container:** Another way is to define a service in docker-compose just to run the saga and exit. For example:

     ```yaml
     saga_runner:
       build: .
       command: python -c "from app import orchestrator; orchestrator.run_saga(2, 'ZoneA')"
       depends_on:
         - celery_worker
     ```

     and then do `docker-compose up saga_runner`. It would execute the saga and finish. However, doing this repeatedly requires re-spawning containers. It might be simpler to just use the existing worker or API approach.

   However you trigger it, once started, the orchestrator will submit tasks to the Celery worker via Redis. You should see logs in the `saga_worker` container for tasks being received and executed (if you run `docker-compose logs -f saga_worker`, you’ll see Celery logs streaming).

4. **Observe Task Execution:** As the Saga runs, you can watch the logs or jump to Flower to see the action:

   * In logs, you’ll see something like:
     `saga_worker ... [INFO] Task app.tasks.allocate_resources[<task-id>] received`
     `saga_worker ... [INFO] Saga[XYZ]: Allocating 2 robots`
     `saga_worker ... [INFO] Saga[XYZ]: Successfully allocated robots`
     `saga_worker ... [INFO] Task app.tasks.allocate_resources[<task-id>] succeeded`
     (And similarly for subsequent tasks).
     If a failure is simulated, you’d see an `ERROR` in logs and a traceback, followed by orchestrator logging the compensation triggers.
   * In **Flower UI**, navigate to `http://<your_server_ip>:5555`. You’ll see the Flower dashboard:

     * The **Tasks** page will list recent tasks by task ID. You can refresh it to see new tasks as they are executed. Each row will show the task name (e.g., `app.tasks.allocate_resources`), the state (STARTED, SUCCESS, or FAILURE), the worker that ran it, runtime, etc.
     * If you click on a task, you can see details like its arguments (e.g., `saga_id`, robot count) and return value or exception traceback. This is very useful to ensure the saga is working as expected.
     * The **Live** view in Flower (if enabled) can live-update tasks in real time.
     * You can also check the **Worker** section in Flower to see the worker status (uptime, queues).

&#x20;*Flower’s web UI provides a real-time view of Celery tasks, showing each task’s state (e.g., pending, started, succeeded, or failed), along with details like task name, arguments, and runtime. In our Saga PoC, as the orchestrator triggers each step, you will see tasks such as `allocate_resources`, `plan_route`, etc., appear in Flower’s task list. If a task fails, it will be highlighted (in red) as **FAILURE**, and the compensation tasks (like `release_resources`) will appear subsequently. This visual feedback helps in debugging and verifying that the Saga flows and rollbacks occur as designed.*

5. **Verify Saga Behavior:** Run multiple tests if needed:

   * Test a successful flow (maybe by configuring no random failures or passing a parameter to not fail). Ensure all steps complete and the saga finishes. In Flower, all tasks should be SUCCESS and you can trace the sequence by timestamp or saga\_id.
   * Test a failure at each stage (you might force failures one by one). For example, configure `plan_route` to raise an exception. Trigger the saga – it should fail at that step, and you should see `release_resources` compensation run afterward. The Flower UI will show `plan_route` as FAILURE, and then a `release_resources` task (triggered by orchestrator) as SUCCESS. The saga stops there (no further steps).
   * Observe that each compensation happened in reverse order of what had succeeded before, as expected in Saga pattern. This demonstrates data consistency is maintained by undoing partial actions.
   * Check the Postgres database (if used) to confirm that state changes correspond to the tasks: e.g., if allocate\_resources inserted a row, and a failure later triggered release\_resources which deleted it, you can query the table to see that no allocation remains after the saga failed.
   * Performance is not a big concern in this PoC, but you can note how Celery handles the tasks quickly and whether any bottlenecks appear.

## Step 6: Monitoring and Debugging the Saga Execution

One of the goals is to see if Celery+Flower provide sufficient **visual information** and debugging capability for a Saga. Here are some tips on using the tools and what to look for:

* **Flower Dashboard:** As shown above, Flower gives a clear list of tasks executed. You can use the search/filter in Flower by task name or state. For example, filter by your saga\_id (if you included it in task arguments) to see all tasks from one saga run grouped together. This is a simple way to trace the flow in the UI. Flower also has a **task timeline** feature (on each task’s detail page) which can show start->end time and the relation if tasks were part of a chain or chord. In our manual orchestration, tasks aren’t formally linked as a chain, so Flower won’t know they were part of one saga transaction – that context is in saga\_id and our code logic. But with saga\_id and timing, you can manually correlate.

* **Logging:** Rely on the logs from the Celery worker and orchestrator. We added logging in tasks (and ideally in the orchestrator) indicating which saga and step is happening. These logs can be aggregated to understand the exact sequence of events. If something doesn’t work as expected, logs will likely reveal it (e.g., an exception stack trace). You can adjust the log level or add more debug logs if needed. Since everything is Dockerized, `docker-compose logs -f saga_worker` (and `saga_api` if used) is your friend for real-time output.

* **Celery Inspector:** Flower allows you to inspect workers and even send control commands (like rate limiting or shutting down workers). For debugging, one relevant feature is the **Broker** page in Flower, which shows the queues and how many tasks are pending. Ideally, during our Saga, the tasks should be processed immediately (not sitting in queue). If you see tasks stuck as pending, it means the worker might be down or mis-routed. Ensure all task names match and the worker is listening on the right queues (by default, Celery listens on the "celery" queue; since we didn’t specify custom queues for tasks, everything uses "celery" queue by default, which is fine).

* **Error Handling:** If a task fails, Celery will capture the exception and store the traceback (since we set `result_extended=True`). Flower will show the **exception message and traceback** for failed tasks. This is extremely useful to debug *why* a task failed (e.g., a coding bug vs. an intentional simulation failure). You should inspect that to ensure failures are expected (for example, our simulated `Exception("Simulated failure")` should appear clearly). If you encounter an unexpected error (say, database connection failed due to wrong env var), you can then fix the config and re-run.

* **Saga State Tracking:** In a more advanced saga, you might have a Saga State object recording what steps completed and what needs compensation. Our PoC uses the code’s logic and immediate compensation triggering, so we don’t persist a saga state. If needed, one could create a `sagas` table in Postgres to insert a record for each saga with status. The orchestrator can update it (e.g., "in progress", "failed at step X", "completed"). That could help if you had an API to query saga status. For now, the Flower UI and logs act as our state tracker.

* **Cleaning Up:** After tests, bring down the stack with:

  ```bash
  docker-compose down
  ```

  This will stop and remove containers. The Postgres volume `pgdata` will persist unless you remove volumes. If you rerun, you may want to clear any residual data or not, depending on if you want a fresh start.

By following these steps, you have set up a complete environment to test the Saga pattern with Celery. You have *free, open-source* infrastructure components (Redis, Postgres, Flower, Celery) orchestrated with Docker Compose for convenience. This lightweight implementation should give you insight into Celery’s capabilities for orchestrating distributed transactions.

## Conclusion and Considerations

In this guide, we walked through creating a Saga Pattern proof-of-concept using Celery. We started from infrastructure setup (Docker containers for Celery, Redis broker, Postgres, and Flower monitoring) and went through writing the Celery tasks and orchestrator to implement an example Saga. By running a multi-step workflow with intentional failures, we demonstrated how Celery can execute the saga steps and how compensating tasks can be triggered to maintain consistency when things go wrong.

**Celery as a Saga Platform:** We find that Celery provides a solid foundation for orchestrating steps – it reliably queues tasks, executes them (even in a distributed fashion if scaled out), and reports their outcomes. The use of Redis as a broker/stream means the overhead is minimal and performance is high for small messages. Celery by itself doesn’t have a built-in Saga controller, so we manually coded the control flow (which is expected, since Saga logic is application-specific and, as literature notes, there’s *no automatic rollback*, the developer must design the compensations). This gave us fine-grained control and also illustrates clearly where complexity can grow (more steps means more compensation logic).

**Visibility and Debugging:** Using Flower greatly enhanced our ability to observe the Saga. We could see each task transition through states and inspect failures in detail. This visual timeline of the Saga’s progress is crucial for debugging. If a Saga spanned many services or took a long time, Flower (or similar tooling) would be indispensable to track it. We saw that by including a `saga_id` in task arguments and logs, we can correlate events belonging to the same saga instance, which is a simple yet effective debugging technique.

**Ease of Use:** Setting up the environment with Docker Compose made it easy to run all components on a single machine. Writing tasks in Python with Celery is straightforward for those familiar with Python. The Saga pattern inherently adds complexity due to the need for compensations, but Celery did not introduce any additional blocking issues – we were able to sequence calls and handle errors in normal Python flow. One caveat: if we had made the orchestrator itself a Celery task, we’d need to be careful to avoid deadlocks (Celery workers waiting on each other). By running the orchestrator externally (via script or API), we sidestepped that issue. This is fine for a PoC. In a real deployment, one might run the orchestrator in a separate service or as part of a web service, as was our optional FastAPI suggestion.

**Potential Improvements:** If we wanted to push this further, we could consider the following:

* Using multiple Celery workers or queues to simulate different microservices (and possibly different failure domains). For example, run separate workers with queues “robot\_service”, “mapping\_service” and route tasks accordingly. This would closer mimic a real distributed system. Our orchestrator can specify `queue=` in `delay()` calls if tasks are tied to specific queues.
* Implementing a Saga log or state in the database (so that if the orchestrator crashes mid-saga, it could theoretically resume or at least we know what was in progress). This is more advanced and often part of robust saga frameworks.
* Exploring Celery’s **retry mechanisms** – Celery can automatically retry failed tasks. We didn’t use that because Saga usually doesn’t blindly retry; it compensates. But for transient failures, a retry might avoid a saga abort. Celery tasks can be declared with a `max_retries` and retry policy.
* Security and configuration hardening: e.g., using Docker secrets for DB password, enabling Flower authentication if deployed publicly, etc., which weren’t necessary for a closed PoC.

**Final Thought:** We set out to see if Celery + Redis + Flower can facilitate a Saga pattern implementation. The result is a functioning demo where we can visually follow a series of operations and their rollbacks. Celery proved to be flexible enough to coordinate the saga, and Flower gave the needed insight into the process. All components used are open-source and free to run on your single server, meeting the project’s requirements. We’ve confirmed that while Celery doesn’t provide a Saga “out-of-the-box”, it gives us the building blocks to implement one. With thoughtful design and the help of monitoring tools, debugging a Saga in Celery is quite feasible – you can watch each step unfold and quickly pinpoint issues. This PoC can serve as a foundation for deeper evaluations, such as performance testing or extending to a more complex workflow, as you continue exploring Saga patterns in distributed systems.
