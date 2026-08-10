"""`status` subcommand (see docs/spec/10-commands/18-status.md).

The spec marks "Expected output format" as ***TBD***; the format below is
a reasonable placeholder pending an authoritative decision (see the
Roadmap note in README.md).
"""
from __future__ import annotations

import os
import sys

from .. import errors, fileops, gitutil, lock, manifest, remote


def build_parser(subparsers):
    parser = subparsers.add_parser(
        "status", help="Show component status (commit drift, pending prunes, local edits)."
    )
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    data, warnings = manifest.load(manifest.manifest_path(root))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    lock_file = lock.lock_path(root)
    if not lock.exists(lock_file):
        if not args.short:
            print("no lock file yet; run 'git component pull' or 'git component resolve'")
        return errors.EXIT_SUCCESS

    lock_data = lock.load(lock_file)
    lock_components = lock_data.get("components", {})

    pending_prune = [name for name in lock_components if name not in data["components"]]
    drifted = _find_drift(data, lock_components)
    modified = _find_local_modifications(root, lock_components)

    if args.short:
        _print_short(drifted, pending_prune, modified)
        return errors.EXIT_SUCCESS

    _print_full(drifted, pending_prune, modified)
    return errors.EXIT_SUCCESS


def _find_drift(data: dict, lock_components: dict) -> list[tuple[str, str, str]]:
    drifted = []
    for name, component in data["components"].items():
        locked = lock_components.get(name)
        if locked is None:
            continue
        try:
            resolved = remote.resolve_commit(component["repository-url"], **manifest.selector(component))
        except errors.GitComponentError as exc:
            drifted.append((name, locked.get("commit"), f"? ({exc})"))
            continue
        if resolved != locked.get("commit"):
            drifted.append((name, locked.get("commit"), resolved))
    return drifted


def _find_local_modifications(root: str, lock_components: dict) -> list[tuple[str, str, str]]:
    modified = []
    for name, locked in lock_components.items():
        for dest, recorded_hash in locked.get("imported-files", {}).items():
            path = os.path.join(root, dest)
            status = fileops.file_status(path)
            if status == "missing":
                modified.append((name, dest, "deleted"))
            elif status == "modified":
                modified.append((name, dest, "replaced-by-directory"))
            elif fileops.sha1_of_file(path) != recorded_hash:
                modified.append((name, dest, "modified"))
    return modified


def _print_short(drifted, pending_prune, modified) -> None:
    for name, _old, _new in drifted:
        print(f"commit-changed {name}")
    for name in pending_prune:
        print(f"pending-prune {name}")
    for name, dest, kind in modified:
        print(f"{kind} {name} {dest}")


def _print_full(drifted, pending_prune, modified) -> None:
    if not (drifted or pending_prune or modified):
        print("up to date")
        return

    if drifted:
        print("Components with a new commit available:")
        for name, old, new in drifted:
            print(f"  {name}: {old} -> {new}")
    if pending_prune:
        print("Components pending prune (removed from the manifest, still present in the lock):")
        for name in pending_prune:
            print(f"  {name}")
    if modified:
        print("Local modifications:")
        for name, dest, kind in modified:
            print(f"  {name}: {dest} ({kind})")
