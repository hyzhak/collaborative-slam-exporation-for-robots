## Brief overview

- Guidelines for implementing features using a strict test-driven development (TDD) workflow for event-driven saga orchestration with Celery and Redis Streams.
- Project-specific rules for incremental, test-first development and documentation.

## Communication style

- Use concise, technical language for all implementation and documentation steps.
- Clearly enumerate next steps and requirements in memory-bank files before starting work.

## Development workflow

- For each new feature or refactor:
  - Start by writing integration tests that define the expected behavior.
  - Run tests to confirm they fail (red state).
  - Implement the feature or change.
  - Run tests again to confirm they pass (green state).
  - Update memory-bank documentation to reflect changes and decisions.
  - Commit changes using Conventional Commits.

## Testing strategies

- Integration tests must cover:
  - Orchestrator triggering on Redis Stream events.
  - Task event emission to Redis Streams.
  - Orchestrator execution as a Celery Canvas workflow.
- Use scripts/integration-tests.sh or docker-compose.test.yaml for test execution.
- Do not merge or deploy code unless all integration tests pass.

## Documentation and commit practices

- Update memory-bank/activeContext.md and memory-bank/progress.md after each major step.
- Use Conventional Commits for all commit messages.
- Document manual validation and troubleshooting steps in README if needed.

## Other guidelines

- Maintain clarity and traceability in all changes and documentation.
