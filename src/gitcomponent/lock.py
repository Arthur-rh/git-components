"""Lock file handling (see docs/spec/03-lock-format.md)."""
from __future__ import annotations

import os
from typing import Any

import yaml

from . import errors

DEFAULT_LOCK_FILENAME = ".git-components.lock"
SUPPORTED_VERSION = 1

RESOLVED_FROM_SELECTORS = ("branch", "tag", "commit")


def lock_path(root: str, override: str | None = None) -> str:
    if override:
        return override if os.path.isabs(override) else os.path.join(root, override)
    return os.path.join(root, DEFAULT_LOCK_FILENAME)


def exists(path: str) -> bool:
    return os.path.isfile(path)


def default_lock() -> dict:
    return {"version": SUPPORTED_VERSION, "components": {}}


def load(path: str) -> dict:
    """Load and validate the lock.

    Raises LockMissingOrInvalidError if the file is missing or fails
    validation (see exit code `21`), or LockUnreadableError if it exists
    but could not be read (exit code `22`).
    """
    if not exists(path):
        raise errors.LockMissingOrInvalidError(f"the lock does not exist: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise errors.LockUnreadableError(f"the lock exists but can not be read: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise errors.LockMissingOrInvalidError(f"the lock is not valid YAML: {exc}") from exc

    validate(data)
    return data


def save(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)
    except OSError as exc:
        raise errors.FilesystemError(f"the lock could not be written: {exc}") from exc


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        raise errors.LockMissingOrInvalidError("the lock YAML is not a mapping")

    if data.get("version") != SUPPORTED_VERSION:
        raise errors.LockMissingOrInvalidError(f"unsupported or missing lock version: {data.get('version')!r}")

    components = data.get("components")
    if not isinstance(components, dict):
        raise errors.LockMissingOrInvalidError("'components' is missing or not a mapping")

    for name, component in components.items():
        if not isinstance(component, dict):
            raise errors.LockMissingOrInvalidError(f"locked component {name!r} is not a mapping")
        if not component.get("repository-url"):
            raise errors.LockMissingOrInvalidError(f"locked component {name!r} lacks 'repository-url'")
        if not component.get("commit"):
            raise errors.LockMissingOrInvalidError(f"locked component {name!r} lacks 'commit'")

        resolved_from = component.get("resolved-from")
        matched = [k for k in RESOLVED_FROM_SELECTORS if isinstance(resolved_from, dict) and k in resolved_from]
        if not isinstance(resolved_from, dict) or len(matched) != 1:
            raise errors.LockMissingOrInvalidError(
                f"locked component {name!r} 'resolved-from' shall contain exactly one of {RESOLVED_FROM_SELECTORS}"
            )

        if "imported-files" not in component:
            raise errors.LockMissingOrInvalidError(f"locked component {name!r} lacks 'imported-files'")
