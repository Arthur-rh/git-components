"""Low-level filesystem helpers used by pull/prune/status.

See docs/spec/03-lock-format.md ("File change detection") and
docs/spec/04-cli.md ("Local modifications").
"""
from __future__ import annotations

import hashlib
import os
import shutil
import stat

from . import errors

READONLY_MODE = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
WRITABLE_MODE = READONLY_MODE | stat.S_IWUSR


def sha1_of_file(path: str) -> str:
    digest = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_writable(path: str) -> None:
    if os.path.exists(path):
        os.chmod(path, WRITABLE_MODE)


def remove_path(path: str) -> None:
    """Remove a file (or, defensively, a directory) that may be read-only."""
    if os.path.islink(path) or os.path.isfile(path):
        make_writable(path)
        os.remove(path)
    elif os.path.isdir(path):
        for root, _dirs, files in os.walk(path):
            for name in files:
                make_writable(os.path.join(root, name))
        shutil.rmtree(path)


def prune_empty_dirs(root: str, start_dir: str) -> None:
    """Remove `start_dir` and any now-empty ancestor directories, stopping at `root`."""
    root = os.path.abspath(root)
    current = os.path.abspath(start_dir)
    while current != root and (current + os.sep).startswith(root + os.sep):
        if not os.path.isdir(current):
            break
        try:
            if os.listdir(current):
                break
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)


def copy_file(src: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    if os.path.exists(dest):
        remove_path(dest)
    shutil.copyfile(src, dest)


def set_readonly(path: str) -> None:
    os.chmod(path, READONLY_MODE)


def file_status(path: str) -> str:
    """Return 'ok', 'modified' (deleted or replaced by a directory), or 'missing'."""
    if not os.path.exists(path):
        return "missing"
    if os.path.isdir(path):
        return "modified"  # a directory replaced a file (see 03-lock-format.md)
    return "ok"


def check_local_modifications(root: str, lock_data: dict, components: list[str] | None = None) -> None:
    """Raise LocalModificationsError if any locked file was changed/deleted locally.

    See docs/spec/03-lock-format.md, "File change detection".
    """
    for name, entry in lock_data.get("components", {}).items():
        if components is not None and name not in components:
            continue
        for dest, recorded_hash in entry.get("imported-files", {}).items():
            path = os.path.join(root, dest)
            status = file_status(path)
            if status == "missing":
                raise errors.LocalModificationsError(f"{dest!r} (component {name!r}) was deleted locally")
            if status == "modified":
                raise errors.LocalModificationsError(
                    f"{dest!r} (component {name!r}) was replaced by a directory"
                )
            if sha1_of_file(path) != recorded_hash:
                raise errors.LocalModificationsError(f"{dest!r} (component {name!r}) was modified locally")
