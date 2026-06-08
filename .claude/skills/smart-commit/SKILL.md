---
description: Commit pending changes as multiple granular, logically grouped commits — asks permission before each commit.
---

Commit all pending changes as multiple granular, logically grouped commits.
Ask for user permission before running each commit command.

## How to group changes

Think about what belongs together by **purpose**, not just by file type:

- A feature implementation + its tests → one commit
- A bug fix touching one file → one commit
- Multiple files that together implement one logical change → one commit
- Documentation / plan updates → one commit (can bundle with .gitignore or other housekeeping)
- Unrelated housekeeping (gitignore, config tweaks) → bundle together or with docs

Never group unrelated features into one commit just to reduce commit count.
Never split a single logical change across multiple commits.

## Process

1. Run `git status` and `git diff --stat` to see what has changed.
2. Inspect the actual diffs (`git diff <file>`) for any file where the purpose isn't obvious from the name.
3. Decide on the grouping. Present the proposed commit plan to the user as a table:

   | # | Files | Proposed commit message |
   |---|-------|------------------------|
   | 1 | ...   | ...                    |

4. For each commit, in order:
   a. Show the exact `git add` + `git commit` commands you are about to run.
   b. **Wait for explicit user approval ("yes", "go ahead", etc.) before running them.**
   c. Run the commands only after approval.
   d. Report the result (short SHA + message).

## Commit message style

- Format: `<type>: <short imperative summary>`
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- First line ≤ 72 characters
- Optional body: 2-4 bullet points with the "what and why" when the change isn't self-evident
- Always append the co-author trailer:
  `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
- Use a heredoc so multi-line messages are passed safely:
  ```
  git commit -m "$(cat <<'EOF'
  feat: short summary here

  - Bullet detail 1
  - Bullet detail 2

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

## What NOT to commit

- `.env` or any file containing secrets
- Large binary files unless explicitly requested
- Files the user has not mentioned and whose purpose is unclear — flag them and ask

## After all commits

Show `git log --oneline -<n>` where n = number of commits just made, so the user can verify the history looks right.
