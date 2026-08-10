"""`status` subcommand (see docs/spec/10-commands/18-status.md).

NOT YET IMPLEMENTED: output format is itself marked ***TBD*** in the spec.
"""
from __future__ import annotations

import sys

from .. import gitutil, manifest

EXIT_NOT_IMPLEMENTED = 99  # placeholder; not part of the spec's exit code table


def build_parser(subparsers):
    parser = subparsers.add_parser(
        "status", help="Show component status (commit drift, pending prunes, local edits)."
    )
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    manifest.load(manifest.manifest_path(root))

    print("git component status: not yet implemented", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED
