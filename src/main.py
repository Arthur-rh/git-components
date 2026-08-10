#!/usr/bin/env python3
"""Dev entry point for running from a source checkout (see docs/spec/04-cli.md).

The installed package instead exposes `git-component` via the
`[project.scripts]` entry point in pyproject.toml (gitcomponent.cli:run_cli).
"""
from gitcomponent.cli import run_cli

if __name__ == "__main__":
    run_cli()
