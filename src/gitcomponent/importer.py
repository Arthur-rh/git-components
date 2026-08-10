"""Materializing component imports into the working tree (see docs/spec/02-manifest-format.md)."""
from __future__ import annotations

import os

from . import errors, patterns


def iter_matching_files(repo_root: str, checkout_dir: str, rule: dict) -> list[tuple[str, str]]:
    """Yield (source_abspath, destination_relpath) pairs for one import rule.

    See "File/folder mapping" and "Filter and exclude semantics" in
    docs/spec/02-manifest-format.md.
    """
    from_ = rule["from"]
    from_trimmed = from_.rstrip("/") or "."
    to_ = rule["to"]
    src_root = os.path.join(checkout_dir, from_trimmed)

    if os.path.isfile(src_root):
        rel = os.path.basename(from_trimmed)
        if not patterns.is_included(rel, rule):
            return []
        if to_.endswith("/"):
            dest = to_ + rel
        elif os.path.isdir(os.path.join(repo_root, to_)):
            dest = to_.rstrip("/") + "/" + rel
        else:
            dest = to_
        return [(src_root, dest.replace(os.sep, "/"))]

    if not os.path.isdir(src_root):
        return []

    if os.path.isfile(os.path.join(repo_root, to_)):
        raise errors.FilesystemError(f"a directory can not be copied inside a file: {from_!r} -> {to_!r}")

    results = []
    for dirpath, _dirnames, filenames in os.walk(src_root):
        for filename in sorted(filenames):
            abspath = os.path.join(dirpath, filename)
            rel = os.path.relpath(abspath, src_root).replace(os.sep, "/")
            if not patterns.is_included(rel, rule):
                continue
            dest = os.path.join(to_, rel).replace(os.sep, "/")
            results.append((abspath, dest))
    return results


def rule_for_dest(component: dict, dest: str) -> tuple[str, str]:
    """Best-effort reverse lookup: which import rule of `component` produced `dest`.

    Used to reconstruct `.gitignore` comments and `suppressed-files` values
    without persisting rule provenance in the lock (the lock schema only
    stores a hash per file, see docs/spec/03-lock-format.md).
    """
    for rule in component.get("imports", []):
        to_ = rule["to"].rstrip("/")
        if dest == to_ or dest.startswith(to_ + "/"):
            return rule["from"], rule["to"]
    return "?", "?"
