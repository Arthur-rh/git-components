"""`remove` subcommand (see docs/spec/10-commands/14-remove.md)."""
from __future__ import annotations

import sys

from .. import errors, gitutil, manifest


def build_parser(subparsers):
    parser = subparsers.add_parser("remove", help="Remove a component from the manifest.")
    parser.add_argument("components", nargs="+")
    parser.add_argument("--manifest", dest="manifest_path")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    path = manifest.manifest_path(root, args.manifest_path)
    data, warnings = manifest.load(path)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    removed = []
    for name in args.components:
        if name not in data["components"]:
            if args.silent:
                continue
            raise errors.ComponentNotFoundError(f"component {name!r} does not exist in the manifest")
        del data["components"][name]
        removed.append(name)

    if removed:
        manifest.save(path, data)

    for name in removed:
        print(
            f"removed component {name!r} from the manifest "
            "(still present in the lock and filesystem; run 'git component prune' to clean up)"
        )
        if args.verbose:
            print(f"updated {path}")

    return errors.EXIT_SUCCESS
