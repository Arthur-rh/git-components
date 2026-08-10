"""`resolve` subcommand (see docs/spec/10-commands/19-resolve.md).

NOT YET IMPLEMENTED: commit-hash resolution requires talking to the
component's remote repository, which is still TODO.
"""
from __future__ import annotations

import sys

from .. import gitutil, manifest

EXIT_NOT_IMPLEMENTED = 99  # placeholder; not part of the spec's exit code table


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
    manifest.load(manifest.manifest_path(root, args.manifest_path))

    print("git component resolve: not yet implemented", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED
