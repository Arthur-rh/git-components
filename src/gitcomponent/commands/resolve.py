"""`resolve` subcommand (see docs/spec/10-commands/19-resolve.md)."""
from __future__ import annotations

import sys

from .. import errors, gitutil, lock, manifest, remote


def build_parser(subparsers):
    parser = subparsers.add_parser(
        "resolve", help="Resolve commit hashes and (re)generate the lock without pulling."
    )
    parser.add_argument("components", nargs="*")
    parser.add_argument("--manifest", dest="manifest_path")
    parser.add_argument("--lock", dest="lock_path")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    data, warnings = manifest.load(manifest.manifest_path(root, args.manifest_path))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    for name in args.components:
        if name not in data["components"]:
            raise errors.ComponentNotFoundError(f"component {name!r} does not exist in the manifest")
    requested = set(args.components) if args.components else None
    selected = [name for name in data["components"] if requested is None or name in requested]

    lock_file = lock.lock_path(root, args.lock_path)
    try:
        lock_data = lock.load(lock_file)
    except errors.GitComponentError:
        lock_data = lock.default_lock()

    lock_components = lock_data.setdefault("components", {})
    lock_data["version"] = lock.SUPPORTED_VERSION

    for name in selected:
        component = data["components"][name]
        component_selector = manifest.selector(component)
        resolved_commit = remote.resolve_commit(component["repository-url"], **component_selector)
        existing = lock_components.get(name, {})

        lock_components[name] = {
            "repository-url": component["repository-url"],
            "commit": resolved_commit,
            "resolved-from": dict(component_selector),
            "imported-files": existing.get("imported-files", {}),
        }
        if existing.get("suppressed-files"):
            lock_components[name]["suppressed-files"] = existing["suppressed-files"]

        selector_key, selector_value = next(iter(component_selector.items()))
        print(f"{name}: {selector_key}={selector_value} -> {resolved_commit}")

    lock.save(lock_file, lock_data)
    return errors.EXIT_SUCCESS
