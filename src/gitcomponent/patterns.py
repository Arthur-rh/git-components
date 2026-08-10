"""Filter/exclude pattern matching (see docs/spec/02-manifest-format.md, "Filter and exclude semantics").

Glob patterns follow gitignore-like semantics: `*` matches within a path
segment, `**` matches across segments (zero or more), `?` matches a single
non-separator character. Matching is always against a path relative to the
import rule's `from` root (see 02-manifest-format.md, "filter-*"/"exclude-*").
"""
from __future__ import annotations

import re


def _glob_to_regex(pattern: str) -> str:
    i, n = 0, len(pattern)
    out = []
    while i < n:
        if pattern[i:i + 2] == "**":
            j = i + 2
            if j < n and pattern[j] == "/":
                out.append("(?:.*/)?")
                j += 1
            else:
                out.append(".*")
            i = j
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "".join(out)


def _glob_match(pattern: str, path: str) -> bool:
    return re.fullmatch(_glob_to_regex(pattern), path) is not None


def _any_match(path: str, glob_patterns, re_patterns) -> bool:
    for pattern in glob_patterns or []:
        if _glob_match(pattern, path):
            return True
    for pattern in re_patterns or []:
        if re.search(pattern, path):
            return True
    return False


def is_included(path: str, rule: dict) -> bool:
    """Whether `path` (relative to the rule's `from`) shall be copied.

    See 02-manifest-format.md: filters are OR'd together; if none are
    specified everything is included (subject to excludes). Excludes are
    OR'd together and applied after filters.
    """
    filter_glob = rule.get("filter-glob")
    filter_re = rule.get("filter-re")
    exclude_glob = rule.get("exclude-glob")
    exclude_re = rule.get("exclude-re")

    if (filter_glob or filter_re) and not _any_match(path, filter_glob, filter_re):
        return False

    if _any_match(path, exclude_glob, exclude_re):
        return False

    return True
