"""`init` subcommand (see docs/spec/10-commands/12-init.md)."""
from __future__ import annotations

from .. import errors, gitutil, manifest


def build_parser(subparsers):
    parser = subparsers.add_parser("init", help="Create an initial .git-components.yml manifest.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing manifest.")
    parser.add_argument("--verbose", action="store_true", help="Display additional information.")
    return parser


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    path = manifest.manifest_path(root)

    if manifest.exists(path) and not args.force:
        raise errors.ManifestAlreadyExistsError(f"manifest already exists at {path} (use --force to overwrite)")

    manifest.create(path)

    if args.verbose:
        print(f"created {path}")

    print(f"Initialized empty git-component manifest at {path}")
    print("Next steps: use 'git component add <name> <repo_url> branch=<name> --map <src>:<dest>' to add a component.")
    return errors.EXIT_SUCCESS
