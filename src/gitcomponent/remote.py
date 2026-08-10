"""Talking to a component's source repository.

See docs/spec/02-manifest-format.md (revision selectors) and
docs/spec/04-cli.md ("Git commit hash resolution", "Credentials" — this
module shells out to the user's `git`, so ambient credentials/helpers apply
unchanged).
"""
from __future__ import annotations

import subprocess

from . import errors


def _run_git(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise errors.GitFailureError(f"git executable not found: {exc}") from exc


def resolve_commit(
    repo_url: str, branch: str | None = None, tag: str | None = None, commit: str | None = None
) -> str:
    """Resolve a branch/tag/commit selector to an exact commit hash.

    See docs/spec/04-cli.md "Git commit hash resolution" and
    docs/spec/02-manifest-format.md "tag" ("shall support lightweight tags").
    A `commit` selector is used directly, as the manifest format says it
    "Indicates an exact commit to use directly".
    """
    if commit:
        return commit

    if branch:
        result = _run_git(["ls-remote", repo_url, f"refs/heads/{branch}"])
        if result.returncode != 0:
            raise errors.GitFailureError(f"could not resolve branch {branch!r} on {repo_url}: {result.stderr.strip()}")
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            raise errors.GitFailureError(f"branch {branch!r} not found on {repo_url}")
        return lines[0].split()[0]

    if tag:
        result = _run_git(["ls-remote", "--tags", repo_url, tag])
        if result.returncode != 0:
            raise errors.GitFailureError(f"could not resolve tag {tag!r} on {repo_url}: {result.stderr.strip()}")

        peeled = None
        direct = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            sha, ref = line.split(maxsplit=1)
            if ref == f"refs/tags/{tag}^{{}}":
                peeled = sha  # annotated tag: use the commit it points to
            elif ref == f"refs/tags/{tag}":
                direct = sha  # lightweight tag: already a commit

        resolved = peeled or direct
        if not resolved:
            raise errors.GitFailureError(f"tag {tag!r} not found on {repo_url}")
        return resolved

    raise errors.ArgumentError("exactly one of branch/tag/commit is required to resolve a commit")


def checkout_commit(repo_url: str, dest: str, commit: str) -> None:
    """Check out `repo_url` at the exact resolved `commit` into `dest`.

    Always checks out by hash (rather than re-resolving branch/tag) so that
    pulls reproduce precisely what was resolved/locked, including under
    `--ignore-manifest` where the locked commit may not be the branch tip.
    """
    result = _run_git(["clone", "--quiet", repo_url, dest])
    if result.returncode != 0:
        raise errors.GitFailureError(f"git clone of {repo_url} failed: {result.stderr.strip()}")

    result = _run_git(["checkout", "--quiet", commit], cwd=dest)
    if result.returncode != 0:
        raise errors.GitFailureError(f"git checkout of {commit} in {repo_url} failed: {result.stderr.strip()}")
