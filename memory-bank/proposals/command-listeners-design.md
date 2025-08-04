# Scalable Command Handlers Proposal

## 1. Background  

As the number of command streams grew, the legacy `app/orchestrator_listener.py` became a bottleneck. This was replaced by a modular, scalable approach where each command stream has its own handler and listener.

## 2. Handler Abstractions  

- Create a new package `app/handlers/`.  
- For each command type, add a module, e.g. `allocate_resources.py`, `plan_route.py`, etc.  
- Each handler module defines:  
  - `STREAM_NAME` (e.g. `"resources:commands"`)  
  - `GROUP_NAME` (e.g. `"resources_handler_group"`)  
  - A `handle(fields: dict) -> None` function that:  
    - Simulates work (`time.sleep(...)`)  
    - Emits logs (`logger.info`)  

## 3. Generic Listener Framework  

- Add `app/command_listener.py`, responsible for:  
  1. Discovering handler modules under `app/handlers/`.  
  2. Spawning one consumer per handler (thread or process).  
  3. For each consumer:  
     - Ensure its Redis consumer group exists.  
     - Loop on `xreadgroup` for that handler’s `STREAM_NAME`.  
     - Call `handler.handle(fields)` and acknowledge the message (`xack`).  

Benefits:  

- New streams are supported by adding a single handler file.  
- Each handler runs independently, improving isolation and failure containment.

## 4. Concurrency & Deployment Models  

**Option A: Multi-handler Service**  

- One container runs `command_listener.py`  
- Spins up N listener threads/processes for each handler  

**Option B: Per-handler Service**  

- Each handler invoked via entrypoint:  

  ```bash
  python -m app.command_listener resources:commands resources_handler_group
  ```  

- Use Docker-compose or Kubernetes to scale each listener independently  

## 5. Future Extensions  

- Swap `time.sleep` for Celery tasks if ordering, retries, or backoff are needed.  
- Expose handler registration via entry-points/plugins for third-party extensions.  
- Add metrics and health-check endpoints per handler.

## 6. Implementation Considerations

The following points are optional enhancements and can guide first or future iterations:

1. Error Handling & Idempotency  
   - Implement retries with backoff or a dead-letter stream for poison messages.  
   - Design handlers to be idempotent so reprocessing does not cause side effects.

2. Consumer Group Management  
   - Ensure group creation is idempotent and handles race conditions (e.g. wrap `XGROUP CREATE` in a try/catch).  
   - Use Redis locks or TTLs on group‐creation keys to avoid duplicate initializations on restarts.

3. Concurrency Model  
   - Prefer separate processes over threads to avoid GIL constraints for CPU-bound work.  
   - Consider an async implementation (asyncio + aioredis) for high-throughput, low-latency scenarios.

4. Backpressure & Flow Control  
   - Introduce rate limiting or a local work queue to prevent slow handlers from blocking other consumers.  
   - Monitor stream length and apply flow control when pending entries exceed thresholds.

5. Configuration & Discovery  
   - Co-locate `STREAM_NAME` and `GROUP_NAME` constants in each handler, discovered via pkgutil/importlib.  
   - Allow runtime overrides via environment variables or CLI flags for flexibility in non-code environments.

6. Observability  
   - Expose per-handler metrics (e.g. processing lag, error counts) via Prometheus or statsd.  
   - Add HTTP health-check endpoints for liveness and readiness probes.

7. Testing Strategy  
   - Unit-test each handler’s logic and error paths.  
   - Write integration tests for `command_listener.py` covering stream reads, acks, retries, and failure scenarios (e.g. Redis downtime).

8. Deployment & Scaling  
   - For per-handler services, document Kubernetes/Docker-Compose examples with anti-affinity and resource limits.  
   - Provide scripts or CI tasks to build and deploy individual handlers without service disruption.

9. Celery Integration Path  
   - Outline a phased migration from in-process handlers to Celery tasks, including parallel support during transition.
