# Subcommand Specification: init

## Synopsis

```bash
git component init [--force] [--verbose]
```

## Purpose

Create an initial `.git-components.yml` manifest in the repository root.

This command is intended to bootstrap use of `git-component`.

## Inputs

- Current working directory **shall** be inside a Git repository

### Options

- `--force`: Overwrite an existing manifest
- `--verbose`: display additional information

## Behavior

The command **shall**:

1. Determine the repository root
2. Check whether `.git-components.yml` already exists
3. If the manifest does not exist, create a new manifest skeleton
4. Print next-step guidance to the user

## Default created manifest

Recommended initial content:

```yaml
version: 1
components: {}
```

## Success conditions

The command succeeds if the repository root is found and the manifest is created successfully.

## Failure conditions

The command **shall** fail if:
- Not inside a Git repository.
- The manifest cannot be written.

The command **shall** fail if:
- The manifest already exists and `--force` is not used.
- Any other filesystem operation fails.

## Side effects

- Creates or overwrites `.git-components.yml`
- **Shall** not perform network operations
- **Shall** not modify imported content

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `4`: any other filesystem error
- `16`: manifest already exists, and `--force` is not used
- `20`: the manifest could not be created