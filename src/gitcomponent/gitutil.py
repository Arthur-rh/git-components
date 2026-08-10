"""Git plumbing helpers (see docs/spec/04-cli.md, "Repository root discovery")."""
from __future__ import annotations

import subprocess

from . import errors


def find_repo_root(start: str | None = None) -> str:
    """Determine the repository root using Git.

    Raises NotAGitRepoError if no repository is found, GitFailureError if
    the git executable itself could not be run.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise errors.GitFailureError(f"git executable not found: {exc}") from exc

    if result.returncode != 0:
        raise errors.NotAGitRepoError(result.stderr.strip() or "not inside a git repository")

    return result.stdout.strip()
