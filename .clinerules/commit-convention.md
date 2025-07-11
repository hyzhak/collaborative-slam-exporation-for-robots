## Brief overview

- Guidelines for commit message conventions in this project.
- All commits must follow the Conventional Commits specification.

## Commit message format

- Use the structure: `<type>(<scope>): <description>`
  - Example: `feat(memory-bank): initialize with projectbrief, productContext, systemPatterns, techContext, activeContext, and progress from design.md`
- Types include: feat, fix, docs, style, refactor, perf, test, chore, build, ci, revert.
- Scope is optional but recommended for clarity (e.g., memory-bank, design, api).

## Additional rules

- Use lowercase for type and scope.
- Description should be concise and in the imperative mood (e.g., "add", "update", "fix").
- Amend or rewrite commits that do not follow this convention before merging.
