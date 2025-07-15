# Development Process Guidelines

## TDD Saga Workflow

- Use strict test-driven development for each new feature or refactor.
- Workflow steps:
  1. Write an integration test defining expected behavior.
  2. Run tests and confirm failure (red).
  3. Implement the feature.
  4. Run tests and confirm success (green).
  5. Update memory-bank documentation (`activeContext.md`, `progress.md`).
  6. Commit changes with Conventional Commits.
