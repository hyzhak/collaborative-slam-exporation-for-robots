# Brief overview

  Compact rules for decorators, mocking, testing, debugging, commits, and tracing.

## Communication style

- Give clear, minimal context.  
- Use temporary debug logs when behavior is unclear; remove them after resolution.

## Decorators & cross-cutting

- Encapsulate boilerplate (events, tracing) in decorators to keep handlers focused.

## Mocking practice

- Patch exactly where functions are used (module namespace), not where they’re defined.
