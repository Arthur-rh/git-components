# Subcommand Specification: help

## Synopsis

```bash
git component help [command]
```

## Purpose

Displays help about git-component in general, or about a specific command

## Inputs

### Arguments
- command (optional): specifies a command to get information about, if the user provides no command, display information about git component.

## Behavior

The command **shall**:

1. Display information about git component or a sub-command of git component

## Success conditions

The command succeeds if:
- either no specific command is given, or if one is given, is a known command

## Failure conditions

The command fails if:
- the specified command is unknown

## Side effects

- **Shall** not modify anything, only write to stdout

## Exit codes

- `0`: success
- `1`: argument validation error
- `6`: the specified command was unknown