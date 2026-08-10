#!/usr/bin/env python3
from pathlib import Path
import re
import sys

PATTERN = re.compile(r"^\d+-.*\.md$")

def concat_matching_files(root="."):
    root_path = Path(root)

    for path in sorted(root_path.rglob("*")):
        if path.is_file() and PATTERN.match(path.name):
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = path.read_text(encoding="latin-1")
                except Exception as e:
                    print(f"# {path}:")
                    print(f"<could not read file: {e}>")
                    print()
                    continue
            except Exception as e:
                print(f"# {path}:")
                print(f"<could not read file: {e}>")
                print()
                continue

            print(f"# {path}:")
            print(content)
            print()

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    concat_matching_files(root)