"""`prune` subcommand (see docs/spec/10-commands/17-prune.md)."""
from __future__ import annotations

import os
import sys

from .. import errors, fileops, gitutil, ignorefile, lock, manifest


def build_parser(subparsers):
    parser = subparsers.add_parser("prune", help="Remove files for components no longer in the manifest.")
    parser.add_argument("components", nargs="*")
    parser.add_argument("--manifest", dest="manifest_path")
    parser.add_argument("--lock", dest="lock_path")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    data, warnings = manifest.load(manifest.manifest_path(root, args.manifest_path))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    lock_file = lock.lock_path(root, args.lock_path)
    lock_data = lock.load(lock_file)
    lock_components = lock_data["components"]

    obsolete = [name for name in lock_components if name not in data["components"]]

    if args.components:
        for name in args.components:
            if name not in lock_components:
                raise errors.ComponentNotFoundError(f"component {name!r} does not exist in the lock")
        obsolete = [name for name in obsolete if name in args.components]

    if not obsolete:
        print("nothing to prune")
        return errors.EXIT_SUCCESS

    if not args.force:
        fileops.check_local_modifications(root, lock_data, components=obsolete)

    for name in obsolete:
        entry = lock_components[name]
        for dest in entry.get("imported-files", {}):
            dest_abspath = os.path.join(root, dest)
            fileops.remove_path(dest_abspath)
            fileops.prune_empty_dirs(root, os.path.dirname(dest_abspath))
        del lock_components[name]
        if args.verbose:
            print(f"pruned component {name!r}")

    lock.save(lock_file, lock_data)

    gitignore_path = os.path.join(root, ".gitignore")
    base_lines = ignorefile.strip_generated_block(ignorefile.read_lines(gitignore_path))
    ignorefile.write(gitignore_path, base_lines, ignorefile.entries_for(data, lock_data))

    print(f"pruned {len(obsolete)} component(s)")
    return errors.EXIT_SUCCESS
