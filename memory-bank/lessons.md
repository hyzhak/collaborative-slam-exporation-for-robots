# Learned Lessons

## File Editing

- Craft precise `replace_in_file` SEARCH blocks matching the exact file content.
- Break large edits into smaller, targeted diffs to improve reliability.

## Celery Canvas & Signatures

- Use `.si` (immutable signatures) for tasks that should not accept previous task results.
- Always supply `correlation_id` and `saga_id` as the first two positional arguments in all task signatures.

## Compensation Patterns

- Attach compensation tasks via `link_error` using a reverse-ordered `chain` for rollback workflows.

## Async Testing Strategies

- Use blocking `xreadgroup` calls and assert on `xpending` to ensure reliable integration tests.
- Validate event emission order and clear pending messages to avoid flakiness.
