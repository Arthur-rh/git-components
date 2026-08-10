# Subcommand Specification: prune

## Synopsis

```bash
git component prune [--force] [--verbose] [--manifest manifest_file] [--lock lock_file] [components...]
```

## Purpose

Removes local components files present in the lock but absent from the manifest (obsolete components), often called after using `remove`

## Inputs

- manifest file is required
- `.git-components.lock` is required

### Arguments

- `components`: (optional) if specified, only prune these components (separated by whitespace).

### Options

- `--manifest <manifest_file>`: specifies a manifest file to use, by default `.git-components.yml`
- `--lock <lock_file>`: specified a lock file to use, by default `.git-components.lock`
- `--force`: bypasses the local file modifications check, this **shall** remove all files even if they were locally modified
- `--verbose`: display additional information

## Core behavior

The command **shall**:

1. Load and validate manifest.
2. Load and validate lock.
3. If one or more component are specified, verify their existence in the lock.
4. List all components present in the lock and missing in the manifest
5. List all files from the mismatched components
6. Check the hashes of the files to be removed for any local modifications, is a file was modified, return an error `7`, unles `--force` is used
7. Remove all files from mismatched components
8. Remove all mismatched components from the lock

## Success conditions

The command succeeds if all selected components are removed successfully and the working tree matches the locked state.

## Failure conditions

The command **shall** fail if:
- The provided manifest or lock does not exist
- The manifest format is invalid (see `02-manifest-format.md`)
- If provided, the component does not exist in the manifest
- The lock format is invalid (see `03-lock-format.md`)
- Any other filesystem operation fails
- A file from a component was modified locally since last pull (hash mismatch), and `--force` is not used.

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `3`: Git failure
- `4`: any other filesystem error
- `7`: files were modified locally since last pull, and `--force` is not used
- `21`: the lock does not exist or is invalid
- `22`: the lock exists but can not be read