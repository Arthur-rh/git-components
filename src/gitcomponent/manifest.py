"""Manifest file handling (see docs/spec/02-manifest-format.md)."""
from __future__ import annotations

import os
import re
from typing import Any

import yaml

from . import errors

DEFAULT_MANIFEST_FILENAME = ".git-components.yml"
SUPPORTED_VERSION = 1

# A single trailing `*` (not `+`) so single-character component names are legal.
COMPONENT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

REVISION_SELECTORS = ("branch", "tag", "commit")

KNOWN_TOP_LEVEL_FIELDS = {"version", "components"}
KNOWN_COMPONENT_FIELDS = {
    "repository-url", "branch", "tag", "commit", "imports", "add-to-gitignore",
}
KNOWN_IMPORT_RULE_FIELDS = {
    "from", "to", "filter-re", "filter-glob", "exclude-re", "exclude-glob",
}

_PATTERN_LIST_FIELDS = ("filter-re", "filter-glob", "exclude-re", "exclude-glob")


def default_manifest() -> dict:
    """Recommended initial content (see docs/spec/10-commands/12-init.md)."""
    return {"version": SUPPORTED_VERSION, "components": {}}


def manifest_path(root: str, override: str | None = None) -> str:
    if override:
        return override if os.path.isabs(override) else os.path.join(root, override)
    return os.path.join(root, DEFAULT_MANIFEST_FILENAME)


def exists(path: str) -> bool:
    return os.path.isfile(path)


def load(path: str, strict: bool = False) -> tuple[dict, list[str]]:
    """Load and validate the manifest.

    Raises ManifestMissingError if the file does not exist, or
    ManifestInvalidError if it exists but cannot be read / fails validation
    (see exit code `18` in docs/spec/04-cli.md, which covers both cases).
    Returns (data, warnings) for unknown-field warnings; if `strict` and
    there are warnings, they are raised as a ManifestInvalidError instead
    (see the global `--strict` option in docs/spec/04-cli.md).
    """
    if not exists(path):
        raise errors.ManifestMissingError(f"the manifest does not exist or is not initialized: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise errors.ManifestInvalidError(f"the manifest exists but could not be read: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise errors.ManifestInvalidError(f"the manifest is not valid YAML: {exc}") from exc

    warnings = validate(data)
    if strict and warnings:
        raise errors.ManifestInvalidError(
            "manifest warnings treated as errors (--strict): " + "; ".join(warnings)
        )

    return data, warnings


def save(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)
    except OSError as exc:
        raise errors.ManifestUneditableError(f"the manifest exists but could not be edited: {exc}") from exc


def create(path: str, data: dict | None = None) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data or default_manifest(), fh, sort_keys=False, default_flow_style=False)
    except OSError as exc:
        raise errors.ManifestUncreatableError(f"the manifest could not be created: {exc}") from exc


def validate(data: Any) -> list[str]:
    """Validate manifest content per the "Validation requirements" section.

    Returns a list of non-fatal warnings (unknown fields). Raises
    ManifestInvalidError for anything that makes the manifest invalid.
    """
    warnings: list[str] = []

    if not isinstance(data, dict):
        raise errors.ManifestInvalidError("the manifest YAML is not a mapping")

    for key in data:
        if key not in KNOWN_TOP_LEVEL_FIELDS:
            warnings.append(f"unknown top-level field: {key!r}")

    version = data.get("version")
    if version != SUPPORTED_VERSION:
        raise errors.ManifestInvalidError(
            f"unsupported or missing manifest version: {version!r} (expected {SUPPORTED_VERSION})"
        )

    components = data.get("components")
    if not isinstance(components, dict):
        raise errors.ManifestInvalidError("'components' is missing or not a mapping")

    for name, component in components.items():
        _validate_component_name(name)
        warnings.extend(_validate_component(name, component))

    return warnings


def _validate_component_name(name: Any) -> None:
    if not isinstance(name, str) or not COMPONENT_NAME_RE.match(name):
        raise errors.ManifestInvalidError(f"invalid component name: {name!r}")


def _validate_component(name: str, component: Any) -> list[str]:
    warnings: list[str] = []

    if not isinstance(component, dict):
        raise errors.ManifestInvalidError(f"component {name!r} is not a mapping")

    for key in component:
        if key not in KNOWN_COMPONENT_FIELDS:
            warnings.append(f"unknown field in component {name!r}: {key!r}")

    if not component.get("repository-url"):
        raise errors.ManifestInvalidError(f"component {name!r} lacks 'repository-url'")

    selectors = [s for s in REVISION_SELECTORS if s in component]
    if len(selectors) != 1:
        raise errors.ManifestInvalidError(
            f"component {name!r} shall define exactly one of {REVISION_SELECTORS}, found {selectors}"
        )

    imports = component.get("imports")
    if not isinstance(imports, list) or not imports:
        raise errors.ManifestInvalidError(f"component {name!r} lacks a non-empty 'imports' list")

    for rule in imports:
        warnings.extend(_validate_import_rule(name, rule))

    add_to_gitignore = component.get("add-to-gitignore", True)
    if not isinstance(add_to_gitignore, bool):
        raise errors.ManifestInvalidError(f"component {name!r}: 'add-to-gitignore' is not a boolean")

    return warnings


def _validate_import_rule(component_name: str, rule: Any) -> list[str]:
    warnings: list[str] = []

    if not isinstance(rule, dict):
        raise errors.ManifestInvalidError(f"component {component_name!r} has a non-mapping import rule")

    for key in rule:
        if key not in KNOWN_IMPORT_RULE_FIELDS:
            warnings.append(f"unknown field in import rule of component {component_name!r}: {key!r}")

    for field in ("from", "to"):
        value = rule.get(field)
        if not isinstance(value, str) or not value:
            raise errors.ManifestInvalidError(f"component {component_name!r} import rule lacks '{field}'")
        if value.startswith("/") or ".." in value.split("/"):
            raise errors.ManifestInvalidError(
                f"component {component_name!r}: '{field}' {value!r} is absolute or escapes the repository root"
            )

    for field in _PATTERN_LIST_FIELDS:
        if field not in rule:
            continue
        patterns = rule[field]
        if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
            raise errors.ManifestInvalidError(f"component {component_name!r}: '{field}' shall be a list of strings")
        if field.endswith("-re"):
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise errors.InvalidPatternError(
                        f"invalid regex {pattern!r} in component {component_name!r}: {exc}"
                    ) from exc

    return warnings
