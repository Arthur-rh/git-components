"""`help` subcommand (see docs/spec/10-commands/11-help.md)."""
from __future__ import annotations

import sys

from .. import errors


def build_parser(subparsers):
    parser = subparsers.add_parser("help", help="Display help about git component or a sub-command.")
    parser.add_argument("command_name", nargs="?", default=None, metavar="command")
    return parser


def run(args, parser) -> int:
    from .. import cli  # deferred: cli imports this module, so avoid a cycle at load time

    if not args.command_name:
        parser.print_help()
        return errors.EXIT_SUCCESS

    sub_parser = cli._SUBPARSERS.get(args.command_name)
    if sub_parser is None:
        print(f"git component help: '{args.command_name}' is not a known command", file=sys.stderr)
        return errors.EXIT_UNKNOWN_COMMAND

    sub_parser.print_help()
    return errors.EXIT_SUCCESS
