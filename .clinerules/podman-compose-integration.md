## Brief overview

- Guidelines for developing, testing, and maintaining infrastructure and code using Podman Compose for local orchestration in this project.

## Podman Compose usage

- Prefer `podman-compose` or `podman compose` for local multi-container orchestration.
- Ensure all docker-compose.yml files are compatible with Podman Compose syntax and behavior.
- When troubleshooting, always check logs for each service individually using `podman logs <container>`.

## Infrastructure development workflow

- After making changes to infrastructure files (docker-compose.yml, Dockerfile, requirements.txt), always rebuild images with `podman-compose build --no-cache` to avoid stale code.
- Use `podman-compose down && podman-compose up -d` to restart the stack after significant changes.
- Confirm all containers are running and healthy with `podman ps -a` before proceeding to application-level testing.

## Commit and documentation practices

- After successful infrastructure changes and verification, commit all related files with a clear, Conventional Commits-compliant message.
- Document any Podman-specific workarounds or requirements in project documentation or Cline rules.
