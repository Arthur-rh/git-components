# Subcommand Specification: status

## Synopsis

```bash
git component status [--short]
```

## Purpose

Similar to `git status`, this command displays information about:
- general information about the current state of the repository (component-wise)
- a commit change (when using branches/tag as reference)
- components waiting to be pruned
- any local modification to a file part of a component

## Inputs

- manifest file is required

### Arguments

- None

### Options

- `--short`: display the information in a much less verbose way, suitable for parsing
- `--verbose`: display additional information

## Core behavior

The command **shall**:

1. Load and validate manifest.
2. If lock is present
   1. Resolve commits from the manifest and report any change
   2. Look for components to be pruned
   3. Compare hashes of all component files
   
## Expected output format

***TBD***

## Success conditions

The command succeeds if all intended information is displayed

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read
- The manifest format is invalid (see `02-manifest-format.md`)
- Any other filesystem operation fails
- Any `git` command fails

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `3`: Git failure
- `17`: the manifest does not exist or is not initialized
- `18`: the manifest exists but could not be read