"""Argument parsing and dispatch (see docs/spec/04-cli.md)."""
from __future__ import annotations

import argparse
import sys

from . import errors
from .commands import add, help as help_cmd, init, list as list_cmd, prune, pull, remove, resolve, status

PROG = "git component"

# Subcommands defined for v1 (see docs/spec/04-cli.md, "Subcommands").
# NOTE: `order` is explicitly NOT part of v1 (see
# docs/spec/10-commands/20-order.md) and is intentionally not registered.
_COMMAND_MODULES = {
    "help": help_cmd,
    "init": init,
    "add": add,
    "remove": remove,
    "pull": pull,
    "prune": prune,
    "list": list_cmd,
    "status": status,
    "resolve": resolve,
}

# Populated by build_parser(); used by the `help` subcommand to print a
# specific sub-parser's help text.
_SUBPARSERS: dict[str, argparse.ArgumentParser] = {}


class _ArgumentParser(argparse.ArgumentParser):
    """Raises ArgumentError (exit code 1) instead of argparse's default exit(2)."""

    def error(self, message):
        raise errors.ArgumentError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=PROG,
        description="Import selected content from external Git repositories using a manifest and a lock.",
    )
    subparsers = parser.add_subparsers(dest="command", parser_class=_ArgumentParser)

    _SUBPARSERS.clear()
    for name, module in _COMMAND_MODULES.items():
        _SUBPARSERS[name] = module.build_parser(subparsers)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = None

    try:
        args = parser.parse_args(argv)

        if not args.command:
            parser.print_help()
            return errors.EXIT_SUCCESS

        module = _COMMAND_MODULES.get(args.command)
        if module is None:
            print(f"git component: '{args.command}' is not a known command", file=sys.stderr)
            return errors.EXIT_UNKNOWN_COMMAND

        return module.run(args, parser=parser)
    except errors.GitComponentError as exc:
        command = getattr(args, "command", None)
        prefix = f"git component {command}" if command else "git component"
        print(f"{prefix}: {exc}", file=sys.stderr)
        return exc.exit_code
