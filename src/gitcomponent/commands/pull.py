"""`pull` subcommand (see docs/spec/10-commands/16-pull.md).

NOT YET IMPLEMENTED: this scaffolds argument parsing per the spec and
reuses the already-implemented manifest loading/validation, but the core
pull/materialization logic ("Core behavior" steps 1-6 in 16-pull.md) is
still TODO.
"""
from __future__ import annotations

import sys

from .. import gitutil, manifest

EXIT_NOT_IMPLEMENTED = 99  # placeholder; not part of the spec's exit code table


def build_parser(subparsers):
    parser = subparsers.add_parser("pull", help="Pull component files to match the manifest/lock.")
    parser.add_argument("components", nargs="*")
    parser.add_argument("--manifest", dest="manifest_path")
    parser.add_argument("--lock", dest="lock_path")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--update-lock", action="store_true")
    parser.add_argument("--ignore-manifest", action="store_true")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    path = manifest.manifest_path(root, args.manifest_path)
    _data, warnings = manifest.load(path, strict=args.strict)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    print("git component pull: not yet implemented", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED
