# Subcommand Specification: resolve

## Synopsis

```bash
git component resolve [components...]
```

## Purpose

Resolves git commit hashes references and generates a lock without pulling files

## Inputs

- manifest file is required

### Arguments

- `components...`: (optional) the name(s) of the component(s) to be resolved, separated by whitespace

### Options

- `--manifest <manifest_file>`: specifies a manifest file to use for resolution
- `--lock <lock_file>`: specifies a lock file to store resolved commit hashes

## Core behavior

The command **shall**:

1. Load and validate manifest.
2. Resolve commit hashes for specified components (or all components)
   
## Expected output format

***TBD***

## Success conditions

The command succeeds if all intended information is displayed

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read
- The manifest format is invalid (see `02-manifest-format.md`)
- Any `git` command fails

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `3`: Git failure
- `17`: the manifest does not exist or is not initialized
- `19`: the manifest exists but could not be edited