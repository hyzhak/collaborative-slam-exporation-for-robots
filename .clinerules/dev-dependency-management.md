# Dependency Management

- Always pin dependencies by listing available versions and updating both `requirements.txt` and `requirements-dev.txt` with exact versions:

```bash
pip index versions <package>
```

  Choose the topmost version and pin it.

- Use a separate development Dockerfile (`Dockerfile.dev`) and a dedicated compose file (`docker-compose.unit.yaml`) for linting and unit tests to keep dev and runtime environments aligned yet isolated.
