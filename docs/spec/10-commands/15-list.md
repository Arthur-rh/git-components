# Subcommand Specification: list

## Synopsis

```bash
git component list [--all] [--silent] [--manifest manifest] [components...]
```

## Purpose

- Lists components specified in argument, or all components if none are specified,
- Displays following information:
  - name of the component
  - reference (branch, tag, commit)

## Inputs

### Arguments

- `components...`: (optional) the name(s) of the component(s) to be displayed, separated by whitespace
  
### Options

- `--all`: displays all information about the components:
  - name of the component
  - repository url
  - reference (branch, tag, commit)
  - file mappings and filters
  - added to .gitignore

- `--silent`: does not return an error if the specified component does not exist

- `--manifest <manifest_file>`: specifies a manifest file to use, by default `.git-components.yml`

## Core behavior

- Lists all components in priority order (up-to-down from the manifest) and displays their information

## Success conditions

The command succeeds only if the information is printed, or if the component does not exist and `--silent` is used

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read.
- The manifest format is invalid (see `02-manifest-format.md`).
- If provided, the component does not exist in the manifest.
- Any other filesystem operation fails.

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `4`: any other filesystem error
- `12`: component does not exist, and `--silent` is not used
- `17`: the manifest does not exist or is not initialized
- `18`: the manifest exists but could not be read, or its content is invalid