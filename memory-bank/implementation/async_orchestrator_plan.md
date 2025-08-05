# Pure Async Orchestrator Implementation Plan

## Overview

Implement a standalone, asyncio-based orchestrator that mirrors the Celery Canvas flow in `app/flows/mission_start_celery/orchestrator.py`, with inline error-handling and compensation logic.

## Step-by-Step Specifications

1. Create directory  
   `app/flows/mission_start_async/`

2. Orchestrator Module
   - File: `app/flows/mission_start_async/orchestrator.py`
   - Imports:  
     • `uuid` and `logging`  
     • `request_and_reply` from `app/redis_utils`  
     • Setup logging via `setup_logging()`
   - Define:
     ```python
     async def run_saga(robot_count, area, correlation_id, fail_steps=None):
         saga_id = …
         logger.info(…)
         # sequential steps with `await request_and_reply(…)`
         # per-step failure injection: if step in fail_steps, raise
         # on exception, invoke inline compensation functions
         # return dict of all step results
     ```
3. Inline Compensation Functions  
   In the same module, add:
   ```python
   async def release_resources(correlation_id, saga_id): …
   async def abort_exploration(correlation_id, saga_id): …
   async def rollback_integration(correlation_id, saga_id): …
   ```
4. Control Flow

   - Execute steps in order: allocate → plan → explore → integrate → release
   - On step failure:  
     • allocate/plan → `await release_resources`  
     • explore → `await abort_exploration` then `await release_resources`  
     • integrate → `await rollback_integration()`, `await abort_exploration()`, then `await release_resources()`
   - After all steps succeed: final `await release_resources`

5. Testing Scaffold
   - File: `tests/integration/test_async_orchestrator.py`
   - Use `request_and_reply` and XREADGROUP to verify:  
     • Correct command and reply streams for each step  
     • Compensation tasks fire on injected failures

## Next Steps

Once this plan is in place, draft the module and test scaffold in Act Mode.
