"""Subcommand implementations, one module per docs/spec/10-commands/*.md file.

Each module exposes:
- build_parser(subparsers) -> argparse.ArgumentParser: registers the subcommand.
- run(args, parser) -> int: executes it and returns an exit code, or raises
  a gitcomponent.errors.GitComponentError.
"""
