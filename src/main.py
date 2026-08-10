#!/usr/bin/env python3
"""Entry point for the git-component CLI (see docs/spec/04-cli.md)."""
import sys

from gitcomponent.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
