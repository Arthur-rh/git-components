"""`prune` subcommand (see docs/spec/10-commands/17-prune.md).

NOT YET IMPLEMENTED: argument parsing and manifest/lock loading are wired
up; the actual pruning ("Core behavior" steps 1-8) is still TODO.
"""
from __future__ import annotations

import sys

from .. import gitutil, lock, manifest

EXIT_NOT_IMPLEMENTED = 99  # placeholder; not part of the spec's exit code table


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
    manifest.load(manifest.manifest_path(root, args.manifest_path))
    lock.load(lock.lock_path(root, args.lock_path))

    print("git component prune: not yet implemented", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED
