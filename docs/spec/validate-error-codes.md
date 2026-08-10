#!/usr/bin/env python3
import os
import re
from collections import defaultdict

# Match lines like:
# - 123: Some message
# (the message is captured as the rest of the line)
LINE_RE = re.compile(r"^\s*-\s*`\s*(?P<code>\d+)\s*`\s*:\s*(?P<message>.*)\s*$")

def iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            # Adjust this if you want to scan other extensions too
            yield os.path.join(dirpath, fn)

def main():
    root = os.getcwd()

    # key: (code, message) -> list of (file, line_no, raw_line)
    seen = defaultdict(list)

    # If you only want markdown specs, uncomment this filter:
    # def should_scan(path): return path.lower().endswith(".md")
    def should_scan(path: str) -> bool:
        return path.lower().endswith(".md")

    for path in iter_files(root):
        if not should_scan(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    m = LINE_RE.match(line.rstrip("\n"))
                    if m:
                        code = m.group("code")
                        message = m.group("message")
                        seen[(code, message)].append((path, i, line.rstrip("\n")))
        except UnicodeDecodeError:
            # Fallback for non-utf8 files
            with open(path, "r", encoding="latin-1") as f:
                for i, line in enumerate(f, start=1):
                    m = LINE_RE.match(line.rstrip("\n"))
                    if m:
                        code = m.group("code")
                        message = m.group("message")
                        seen[(code, message)].append((path, i, line.rstrip("\n")))

    if not seen:
        print("No error-code patterns found in any *.md files.")
        return

    # Sort for stable output
    items = sorted(seen.items(), key=lambda kv: (int(kv[0][0]), kv[0][1]))

    for (code, message), occurrences in items:
        print(f"`{code}`: {message}")
        for (path, line_no, _raw) in occurrences:
            print(f"  - {path}:{line_no}")
        print()

if __name__ == "__main__":
    main()