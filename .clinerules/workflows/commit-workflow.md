<task name="Commit changes">

<task_objective>
Commit changes from the respository by follow precise steps. By provided informative title for the commit.
</task_objective>

<detailed_sequence_steps>

# Cline Commit Workflow - Detailed Sequence of Steps

## 1. Review Changes

- Run `git status` to see modified and staged files.

## 2. Check Diffs for Insights

- Use `git diff <file>` or `git --no-pager diff` to review the exact changes in each file before staging.
- After staging, run `git diff --cached` (or `git --no-pager diff --cached`) to verify exactly what will be committed.
- This helps you understand and verify what was changed, and catch any unintended edits.

## 3. Stage Changes

- Stage only the files you intend to commit:
  ```bash
  git add <file1> <file2> ...
  ```

## 4. Commit

- Use the Conventional Commits format:
  ```bash
  git commit -m "<type>(<scope>): <short description>"
  ```
- Example:
  ```bash
  git commit -m "chore(async-orchestrator): remove unused imports and obsolete integration test"
  ```

## 5. Pager Configuration (Optional)

- To globally disable paging for all git commands:
  ```bash
  git config --global core.pager cat
  ```

## 6. Best Practices

- Keep commits small and focused.
- Use imperative mood in commit messages.
- Add a descriptive body if the change is non-trivial.
- Proactively research and verify context without asking for human confirmation.
- Only request human input in unusual or ambiguous situations.

</detailed_sequence_steps>
</task>
