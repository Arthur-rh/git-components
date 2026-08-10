# Subcommand Specification: remove

## Synopsis

```bash
git component remove [--silent] [--manifest manifest] [--verbose] <components...>
```

## Purpose

Removes the component from the manifest.

## Inputs

### Arguments

- `components`: the name(s) of the component(s) to be removed from the manifest, (separated by any whitespace) there **shall** be at least 1 component

### Options

- `--manifest <manifest_file>`: specifies a manifest file to use, by default `.git-components.yml`
- `--silent`: when this option is used, the command does not return an error if the component does not exist
- `--verbose`: display additional information

## Core behavior

When removing a component from the manifest, the command **shall** :

- verify that the component exists
- remove the entry from the manifest
- notify user that the component was removed from the manifest but is still present in the lock and filesystem, and invite the user to run `git component prune`

## Success conditions

The command succeeds if the component was removed from the manifest.

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read
- The manifest format is invalid (see `02-manifest-format.md`)
- The component does not exist in the manifest, and `--silent` is not used
- Any other filesystem operation fails

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `4`: any other filesystem error
- `12`: component does not exist, and `--silent` is not used
- `17`: the manifest does not exist or is not initialized
- `18`: the manifest exists but could not be read, or its content is invalid
- `19`: the manifest exists but could not be edited