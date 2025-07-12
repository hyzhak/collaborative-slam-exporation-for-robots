## Brief overview

- Guidelines for ensuring code quality and reliability in this project, with a focus on integration testing and validation before merging or deploying changes.

## Test-driven development and validation

- Any code changes (features, bugfixes, refactors) must be validated by running the integration test suite before merging or deployment.
- Integration tests are defined in `tests/` and executed via the helper script (`./scripts/integration-tests.sh`), Podman Compose, or Docker Compose.
- If new features or bugfixes are added, corresponding tests should be created or updated to cover them.
- Pull requests and code reviews should include a statement confirming that integration tests have passed.

## Communication and documentation

- Update the README or relevant documentation to reflect changes in the testing workflow or requirements.
- Clearly document any new test cases or changes to test structure.

## Coding and commit practices

- Follow Conventional Commits for all commit messages.
- Ensure that all code pushed to shared branches has been validated by a successful test run.

## Other guidelines

- If integration tests fail, do not merge or deploy until the failure is resolved.
- Encourage a culture of automated validation to maintain project reliability.
