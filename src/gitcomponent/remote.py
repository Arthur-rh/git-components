"""Talking to a component's source repository.

See docs/spec/02-manifest-format.md (revision selectors) and
docs/spec/04-cli.md ("Git commit hash resolution", "Credentials" — this
module shells out to the user's `git`, so ambient credentials/helpers apply
unchanged).

Checked-out content is materialized from a local mirror cache (one bare
`--mirror` clone per distinct `repository-url`, stored under the
destination repository's `.git/`) rather than a fresh full clone on every
pull: the mirror is only cloned once and thereafter updated with a plain
`git fetch`, and only when the resolved commit isn't already present
locally.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile

from . import errors

CACHE_DIRNAME = "git-components-cache"


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


def _cache_dir_for(git_dir: str, repo_url: str) -> str:
    digest = hashlib.sha1(repo_url.encode("utf-8")).hexdigest()
    return os.path.join(git_dir, CACHE_DIRNAME, digest)


def _ensure_cache(git_dir: str, repo_url: str) -> str:
    """Return a local bare mirror of `repo_url`, cloning it if not already cached.

    Clones into a sibling temp directory first and renames into place, so a
    clone that fails partway never leaves a broken directory that a later
    run would mistake for a valid cache.
    """
    cache_dir = _cache_dir_for(git_dir, repo_url)
    if os.path.isdir(cache_dir):
        return cache_dir

    cache_root = os.path.dirname(cache_dir)
    os.makedirs(cache_root, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache_root, prefix="tmp-") as tmp:
        clone_target = os.path.join(tmp, "mirror")
        result = _run_git(["clone", "--quiet", "--mirror", repo_url, clone_target])
        if result.returncode != 0:
            raise errors.GitFailureError(f"git clone --mirror of {repo_url} failed: {result.stderr.strip()}")
        os.replace(clone_target, cache_dir)

    return cache_dir


def _fetch_cache(cache_dir: str, repo_url: str) -> None:
    result = _run_git(["fetch", "--quiet", "--prune", "origin"], cwd=cache_dir)
    if result.returncode != 0:
        raise errors.GitFailureError(f"git fetch of {repo_url} (cache: {cache_dir}) failed: {result.stderr.strip()}")


def _commit_exists(cache_dir: str, commit: str) -> bool:
    result = _run_git(["cat-file", "-e", f"{commit}^{{commit}}"], cwd=cache_dir)
    return result.returncode == 0


def checkout_commit(git_dir: str, repo_url: str, dest: str, commit: str) -> None:
    """Materialize `repo_url` at the exact resolved `commit` into `dest`.

    Always checks out by hash (rather than re-resolving branch/tag) so that
    pulls reproduce precisely what was resolved/locked, including under
    `--ignore-manifest` where the locked commit may not be the branch tip.
    Uses the local mirror cache (see module docstring) and `git archive` to
    extract the tree directly, without an intermediate working-tree clone.
    """
    cache_dir = _ensure_cache(git_dir, repo_url)

    if not _commit_exists(cache_dir, commit):
        _fetch_cache(cache_dir, repo_url)
        if not _commit_exists(cache_dir, commit):
            raise errors.GitFailureError(f"commit {commit!r} not found in {repo_url} (cache: {cache_dir})")

    os.makedirs(dest, exist_ok=True)
    try:
        proc = subprocess.Popen(
            ["git", "archive", "--format=tar", commit],
            cwd=cache_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise errors.GitFailureError(f"git executable not found: {exc}") from exc

    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            tar.extractall(dest)  # Python < 3.12: `filter=` isn't available yet

    stderr = proc.stderr.read()
    proc.stdout.close()
    proc.stderr.close()
    if proc.wait() != 0:
        raise errors.GitFailureError(
            f"git archive of {commit} in {repo_url} failed: {stderr.decode(errors='replace').strip()}"
        )
