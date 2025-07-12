import uuid
import logging
from app.celery_app import celery_app
from app.tasks import (
    allocate_resources,
    plan_route,
    perform_exploration,
    integrate_maps,
    release_resources,
    abort_exploration,
    rollback_integration,
)

logger = logging.getLogger(__name__)

def run_saga(robot_count, area, fail_steps=None):
    """
    fail_steps: optional set/list of step names to force failure for testing, e.g. {"allocate_resources"}
    """
    saga_id = str(uuid.uuid4())[:8]
    fail_steps = set(fail_steps or [])
    logger.info(f"Saga[{saga_id}]: Starting saga with {robot_count} robots in area '{area}'")
    try:
        # Step 1: Allocate resources
        res1 = allocate_resources.delay(saga_id, robot_count, fail="allocate_resources" in fail_steps)
        result1 = res1.get(timeout=10)
        # Step 2: Plan route
        res2 = plan_route.delay(saga_id, area, fail="plan_route" in fail_steps)
        result2 = res2.get(timeout=10)
        # Step 3: Perform exploration
        res3 = perform_exploration.delay(saga_id, robot_count, fail="perform_exploration" in fail_steps)
        result3 = res3.get(timeout=20)
        # Step 4: Integrate maps
        res4 = integrate_maps.delay(saga_id, fail="integrate_maps" in fail_steps)
        result4 = res4.get(timeout=10)
        logger.info(f"Saga[{saga_id}]: Completed successfully. Final map: {result4['final_map']}")
        # Optionally release resources at end
        release_resources.delay(saga_id)
    except Exception as e:
        logger.error(f"Saga[{saga_id}]: Failed: {e}")
        # Compensation logic in reverse order
        if "integrate_maps" in fail_steps:
            rollback_integration.delay(saga_id)
            abort_exploration.delay(saga_id)
            release_resources.delay(saga_id)
        elif "perform_exploration" in fail_steps:
            abort_exploration.delay(saga_id)
            release_resources.delay(saga_id)
        elif "plan_route" in fail_steps:
            release_resources.delay(saga_id)
        elif "allocate_resources" in fail_steps:
            pass  # nothing to compensate
        logger.info(f"Saga[{saga_id}]: Compensation dispatched due to failure.")

if __name__ == "__main__":
    # Example usage: run_saga(2, "ZoneA", fail_steps={"plan_route"})
    import sys
    import ast
    robot_count = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    area = sys.argv[2] if len(sys.argv) > 2 else "ZoneA"
    fail_steps = ast.literal_eval(sys.argv[3]) if len(sys.argv) > 3 else set()
    run_saga(robot_count, area, fail_steps)
