# Cline Commit Workflow

## 1. Review Changes

- Run `git status` to see modified and staged files.

## 2. Check Diffs for Insights

- Use `git diff <file>` or `git --no-pager diff` to review the exact changes in each file before staging.
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
  git commit -m "chore(test,compose): remove unused imports and fix volume mount"
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
