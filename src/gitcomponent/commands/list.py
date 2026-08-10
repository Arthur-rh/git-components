"""`list` subcommand (see docs/spec/10-commands/15-list.md)."""
from __future__ import annotations

import sys

from .. import errors, gitutil, manifest


def build_parser(subparsers):
    parser = subparsers.add_parser("list", help="List configured components.")
    parser.add_argument("components", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--manifest", dest="manifest_path")
    return parser


def _reference(component: dict) -> str:
    for key in ("branch", "tag", "commit"):
        if key in component:
            return f"{key}={component[key]}"
    return "?"


def _print_component(name: str, component: dict, show_all: bool) -> None:
    print(f"{name}\t{_reference(component)}")
    if not show_all:
        return

    print(f"  repository-url: {component.get('repository-url')}")
    print(f"  add-to-gitignore: {component.get('add-to-gitignore', True)}")
    for rule in component.get("imports", []):
        print(f"  - from: {rule.get('from')} -> to: {rule.get('to')}")
        for field in ("filter-glob", "filter-re", "exclude-glob", "exclude-re"):
            if field in rule:
                print(f"      {field}: {rule[field]}")


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    path = manifest.manifest_path(root, args.manifest_path)
    data, warnings = manifest.load(path)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    names = args.components or list(data["components"].keys())

    for name in names:
        component = data["components"].get(name)
        if component is None:
            if args.silent:
                continue
            raise errors.ComponentNotFoundError(f"component {name!r} does not exist in the manifest")
        _print_component(name, component, args.all)

    return errors.EXIT_SUCCESS
