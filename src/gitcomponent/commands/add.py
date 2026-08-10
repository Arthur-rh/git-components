"""`add` subcommand (see docs/spec/10-commands/13-add.md)."""
from __future__ import annotations

import argparse
import re
import sys

from .. import errors, gitutil, manifest


class _RecordMapOp(argparse.Action):
    """Appends (flag, value) tuples in command-line order.

    Needed because --filter-*/--exclude-* options are only valid when they
    immediately follow --map or another --filter-*/--exclude-* option (see
    the spec's "IMPORTANT NOTE" under `add`'s Options), which plain argparse
    dest-per-flag storage cannot express.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        ops = getattr(namespace, "map_ops", None) or []
        ops.append((option_string, values))
        namespace.map_ops = ops


def build_parser(subparsers):
    parser = subparsers.add_parser("add", help="Add a component into the manifest.")
    parser.add_argument("component_name")
    parser.add_argument("repo_url")
    parser.add_argument("reference", help="branch=<name> | tag=<name> | commit=<hash>")
    parser.add_argument("--manifest", dest="manifest_path")
    parser.add_argument("--map", dest="map_ops", action=_RecordMapOp, metavar="src:dest")
    parser.add_argument("--filter-glob", dest="map_ops", action=_RecordMapOp, metavar="pattern")
    parser.add_argument("--filter-re", dest="map_ops", action=_RecordMapOp, metavar="pattern")
    parser.add_argument("--exclude-glob", dest="map_ops", action=_RecordMapOp, metavar="pattern")
    parser.add_argument("--exclude-re", dest="map_ops", action=_RecordMapOp, metavar="pattern")
    parser.add_argument("--no-gitignore", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def _parse_reference(raw: str) -> dict:
    key, _, value = raw.partition("=")
    if key not in ("branch", "tag", "commit") or not value:
        raise errors.ArgumentError(f"invalid reference {raw!r}: shall be branch=<name>, tag=<name>, or commit=<hash>")
    return {key: value}


_FIELD_BY_FLAG = {
    "--filter-glob": "filter-glob",
    "--filter-re": "filter-re",
    "--exclude-glob": "exclude-glob",
    "--exclude-re": "exclude-re",
}


def _build_imports(map_ops: list[tuple[str, str]]) -> list[dict]:
    """Turn the ordered --map/--filter-*/--exclude-* tokens into import rules."""
    imports: list[dict] = []
    current: dict | None = None

    for flag, value in map_ops:
        if flag == "--map":
            if ":" not in value:
                raise errors.ArgumentError(f"--map value {value!r} shall be src:dest")
            src, _, dest = value.partition(":")
            current = {"from": src, "to": dest}
            imports.append(current)
            continue

        if current is None:
            raise errors.UnexpectedFilterOptionError(
                f"{flag} shall always follow a --map or another --filter-*/--exclude-* option"
            )

        field = _FIELD_BY_FLAG[flag]
        if field.endswith("-re"):
            try:
                re.compile(value)
            except re.error as exc:
                raise errors.InvalidPatternError(f"invalid regex {value!r}: {exc}") from exc

        current.setdefault(field, []).append(value)

    return imports


def run(args, parser) -> int:
    root = gitutil.find_repo_root()
    path = manifest.manifest_path(root, args.manifest_path)

    if not manifest.exists(path):
        raise errors.ManifestMissingError(f"the manifest does not exist or is not initialized: {path}")

    data, warnings = manifest.load(path)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if not manifest.COMPONENT_NAME_RE.match(args.component_name):
        raise errors.ArgumentError(f"invalid component name: {args.component_name!r}")

    if args.component_name in data["components"] and not args.force:
        raise errors.ComponentAlreadyPresentError(
            f"component {args.component_name!r} is already present (use --force to overwrite)"
        )

    imports = _build_imports(args.map_ops or [])
    if not imports:
        raise errors.ArgumentError("at least one --map src:dest is required")

    component: dict = {
        "repository-url": args.repo_url,
        **_parse_reference(args.reference),
        "imports": imports,
    }
    if args.no_gitignore:
        component["add-to-gitignore"] = False

    data["components"][args.component_name] = component
    manifest.save(path, data)

    if args.verbose:
        print(f"added component {args.component_name!r} to {path}")

    return errors.EXIT_SUCCESS
