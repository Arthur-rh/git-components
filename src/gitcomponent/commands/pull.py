"""`pull` subcommand (see docs/spec/10-commands/16-pull.md)."""
from __future__ import annotations

import os
import sys
import tempfile

from .. import errors, fileops, gitutil, ignorefile, importer, lock, manifest, remote


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
    manifest_file = manifest.manifest_path(root, args.manifest_path)
    lock_file = lock.lock_path(root, args.lock_path)

    data, warnings = manifest.load(manifest_file, strict=args.strict)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    for name in args.components:
        if name not in data["components"]:
            raise errors.ComponentNotFoundError(f"component {name!r} does not exist in the manifest")
    requested = set(args.components) if args.components else None
    selected = [name for name in data["components"] if requested is None or name in requested]

    try:
        lock_data = lock.load(lock_file)
    except errors.GitComponentError:
        lock_data = lock.default_lock()

    lock_components = lock_data.setdefault("components", {})
    lock_data["version"] = lock.SUPPORTED_VERSION

    if not args.force:
        fileops.check_local_modifications(root, lock_data)

    _resolve_commits(data, selected, lock_components, args)

    priority = {name: index for index, name in enumerate(data["components"])}
    owners = _current_owners(lock_data, priority)

    for name in selected:
        component = data["components"][name]
        entry = lock_components[name]

        # steps 6.2/6.3: drop this component's previous files before re-copying
        for dest in list(entry.get("imported-files", {})):
            dest_abspath = os.path.join(root, dest)
            fileops.remove_path(dest_abspath)
            fileops.prune_empty_dirs(root, os.path.dirname(dest_abspath))
            owners.pop(dest, None)
        entry["imported-files"] = {}
        entry.pop("suppressed-files", None)

        with tempfile.TemporaryDirectory(prefix="git-component-") as checkout_dir:
            remote.checkout_commit(component["repository-url"], checkout_dir, entry["commit"])
            imported, suppressed = _materialize(
                root, checkout_dir, name, component, priority[name], owners, data["components"], lock_components
            )

        entry["imported-files"] = imported
        if suppressed:
            entry["suppressed-files"] = suppressed

        if args.verbose:
            print(f"{name}: imported {len(imported)} file(s)")

    lock.save(lock_file, lock_data)

    gitignore_path = os.path.join(root, ".gitignore")
    base_lines = ignorefile.strip_generated_block(ignorefile.read_lines(gitignore_path))
    ignorefile.write(gitignore_path, base_lines, ignorefile.entries_for(data, lock_data))

    print(f"pulled {len(selected)} component(s)")
    return errors.EXIT_SUCCESS


def _resolve_commits(data: dict, selected: list[str], lock_components: dict, args) -> None:
    """Commit resolution rules (see docs/spec/10-commands/16-pull.md)."""
    for name in selected:
        component = data["components"][name]
        component_selector = manifest.selector(component)
        existing = lock_components.get(name)

        if args.ignore_manifest and existing:
            continue  # keep the lock's existing resolution untouched

        resolved_commit = remote.resolve_commit(component["repository-url"], **component_selector)

        if existing and existing.get("commit") != resolved_commit and not args.update_lock:
            raise errors.ManifestLockDisagreeError(
                f"component {name!r}: manifest resolves to {resolved_commit!r} but the lock has "
                f"{existing.get('commit')!r} (use --update-lock or --ignore-manifest)"
            )

        lock_components[name] = {
            "repository-url": component["repository-url"],
            "commit": resolved_commit,
            "resolved-from": dict(component_selector),
            "imported-files": (existing or {}).get("imported-files", {}),
        }
        if existing and existing.get("suppressed-files"):
            lock_components[name]["suppressed-files"] = existing["suppressed-files"]


def _current_owners(lock_data: dict, priority: dict) -> dict:
    """dest_path -> (priority_index, component_name) for every currently-imported file."""
    owners = {}
    for name, entry in lock_data.get("components", {}).items():
        if name not in priority:
            continue  # obsolete component (left for `prune`); not a priority contender
        for dest in entry.get("imported-files", {}):
            owners[dest] = (priority[name], name)
    return owners


def _materialize(root, checkout_dir, name, component, priority_index, owners, all_components, lock_components):
    """Copy one component's files, applying the conflict-resolution rules from the spec.

    See "Conflict handling" in docs/spec/10-commands/16-pull.md and
    "Priority order" in docs/spec/02-manifest-format.md.
    """
    imported: dict[str, str] = {}
    suppressed: dict[str, str] = {}
    claimed_this_component: set[str] = set()

    for rule in component["imports"]:
        for src_abspath, dest in importer.iter_matching_files(root, checkout_dir, rule):
            if dest in claimed_this_component:
                print(
                    f"warning: component {name!r}: multiple import rules target {dest!r}; "
                    "keeping the higher-priority rule",
                    file=sys.stderr,
                )
                continue

            owner = owners.get(dest)
            if owner is not None:
                owner_priority, owner_name = owner
                if owner_priority < priority_index:
                    owner_from, owner_to = importer.rule_for_dest(all_components[owner_name], dest)
                    suppressed[dest] = f"{owner_name}@{owner_from}:{owner_to}"
                    print(
                        f"warning: component {name!r}: {dest!r} is already imported by "
                        f"higher-priority component {owner_name!r}; skipping",
                        file=sys.stderr,
                    )
                    continue
                if owner_priority > priority_index:
                    fileops.remove_path(os.path.join(root, dest))
                    loser_entry = lock_components.get(owner_name)
                    if loser_entry is not None:
                        loser_entry.get("imported-files", {}).pop(dest, None)
                        loser_entry.setdefault("suppressed-files", {})[dest] = f"{name}@{rule['from']}:{rule['to']}"
                    print(
                        f"warning: component {name!r} overwrites {dest!r}, previously imported by "
                        f"lower-priority component {owner_name!r}",
                        file=sys.stderr,
                    )

            dest_abspath = os.path.join(root, dest)
            fileops.copy_file(src_abspath, dest_abspath)
            fileops.set_readonly(dest_abspath)

            imported[dest] = fileops.sha1_of_file(dest_abspath)
            claimed_this_component.add(dest)
            owners[dest] = (priority_index, name)

    return imported, suppressed
