# Subcommand Specification: add

## Synopsis

```bash
git component add <component_name> <repo_url> branch=<branch_name>|tag=<tag_name>|commit=<commit_hash> [--manifest manifest] [--map src:dest] [--filter-glob pattern] [--filter-re pattern] [--exclude-glob pattern] [--exclude-re pattern] [--no-gitignore] [--force] [--verbose]
```

## Purpose

Adds the component into the manifest, by default `.git-components.yml`

## Inputs

### Arguments

- component_name: the name of the component, **shall** match regex `[A-Za-z_][A-Za-z0-9_-]+`
- repo_url: the url of the repository where the component lives
- reference: the reference to use, has to be exactly one of either
  - branch=<branch_name>
  - tag=<tag_name>
  - commit=<commit_hash>

### Options

- `--manifest <manifest_file>`: file to store the component, `.git-components.yml` by default
- `--map <src>:<dest>`: file/directory mapping between the source (original repository) to the destination
  - Multiple mappings can be specified, the order of priority of the mapping **shall** be order in which the `--map ...` options are passed 
- `--filter-glob/--filter-re <pattern>`: adds a regex/glob rule to only include files/folders to the previous mappping.
- `--exclude-glob/--exclude-re <pattern>`: adds a regex/glob rule to exclude files/folders to the previous mapping.
  - **IMPORTANT NOTE**: the `--filter-*` or `--exclude-*` options **shall** ALWAYS follow a `--map src:dest` option or another `--filter-*` or `--exclude-*` option, and **shall** return an error otherwise
  - Multiple `--filter-*` or `--exclude-*` options can be placed after a `--map` to specify multiple patterns, each rule **shall** be checked against the mapping with an `OR` operator between all rules
- `--no-gitignore`: The added component **shall** not be added to the current repository `.gitignore`
- `--force`: overwrites the entry if a component is already present in the manifest
- `--verbose`: display additional information

## Core behavior

When adding a component to the manifest, the command **shall** :

- validate inputs
- verify that the component is not already present, otherwise return an error if `--force` is not present
- add the component to the manifest

## Success conditions

- The command succeeds if the component was added in the manifest.

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read
- The manifest format is invalid (see `02-manifest-format.md`)
- The provided pattern is not a valid regex
- The component already exists and the `--force` option is not used.
- Any other filesystem operation fails
- There is any unexpected usage of option `--filter-glob/filter-re/exclude-glob/exclude-re pattern`

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `4`: any other filesystem error
- `5`: the given regex/glob pattern is not valid
- `8`: unexpected usage of option `--filter-glob/filter-re/exclude-glob/exclude-re pattern`
- `11`: component is already present, and `--force` is not used
- `17`: the manifest does not exist or is not initialized
- `19`: the manifest exists but could not be edited