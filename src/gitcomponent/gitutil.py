"""Git plumbing helpers (see docs/spec/04-cli.md, "Repository root discovery")."""
from __future__ import annotations

import os
import subprocess

from . import errors


def _rev_parse(args: list[str], start: str | None) -> str:
    try:
        result = subprocess.run(["git", "rev-parse", *args], cwd=start, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise errors.GitFailureError(f"git executable not found: {exc}") from exc

    if result.returncode != 0:
        raise errors.NotAGitRepoError(result.stderr.strip() or "not inside a git repository")

    return result.stdout.strip()


def find_repo_root(start: str | None = None) -> str:
    """Determine the repository root using Git.

    Raises NotAGitRepoError if no repository is found, GitFailureError if
    the git executable itself could not be run.
    """
    return _rev_parse(["--show-toplevel"], start)


def find_git_dir(start: str | None = None) -> str:
    """Determine the repository's common `.git` directory (shared across worktrees).

    Used to place the local clone cache (see remote.py) somewhere stable and
    already excluded from the destination repository's own tracked content.
    """
    git_dir = _rev_parse(["--git-common-dir"], start)
    return git_dir if os.path.isabs(git_dir) else os.path.join(os.path.abspath(start or os.getcwd()), git_dir)
