# Cline Commit Workflow

## 1. Review Changes

- Run `git status` to see modified and staged files.
- Use `git --no-pager diff` (or set `GIT_PAGER=cat`) to view full diffs without a pager blocking the terminal.

## 2. Stage Changes

- Stage only the files you intend to commit:
  ```bash
  git add <file1> <file2> ...
  ```

## 3. Commit

- Use the Conventional Commits format:
  ```bash
  git commit -m "<type>(<scope>): <short description>"
  ```
- Example:
  ```bash
  git commit -m "chore(test,compose): remove unused imports and fix volume mount"
  ```

## 4. Pager Configuration (Optional)

- To globally disable paging for all git commands:
  ```bash
  git config --global core.pager cat
  ```

## 5. Best Practices

- Keep commits small and focused.
- Use imperative mood in commit messages.
- Add a descriptive body if the change is non-trivial.
