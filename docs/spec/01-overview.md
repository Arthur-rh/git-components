# git-component Specification Overview

## Purpose

`git-component` is a command-line tool for importing selected content from external Git repositories into the current repository, using a declarative manifest and a lock.

It is conceptually similar to `git subtree` in that external repository content becomes ordinary files in the working tree, but differs in that:

- the manifest defines the content to import
- only selected paths **may** be imported
- imports can be filtered and excluded by patterns
- imports are not tracked by the repository they are part of
- exact revisions (commit hashes) are recorded in a lock for reproducibility

## Scope

This specification defines:

- the role of the manifest file (by default `.git-components.yml`)
- the role of the lock file (by default `.git-components.lock`)
- the CLI behavior of `git component`
- validation and synchronization rules
- subcommand semantics

This specification does not require a specific implementation language.

## Terminology

### Component
A named dependency defined in `.git-components.yml` that references an external Git repository and one or more import mappings.

### Manifest
The file `.git-components.yml`, which defines the desired state.

### Lock file
The file `.git-components.lock`, which records the exact resolved commit for each component and information about the current state of the repository components and their files.

### Import rule
A mapping from a path inside the source repository at to a destination path in the current repository, can also contain a filter and exclusion rule.

### Resolved commit
The exact Git commit hash selected for a component after resolving a branch, tag, or explicit commit.

## High-level model

A component definition includes:

- repository location
- revision selector
- one or more import rules

An import rule defines:

- source path (`from`)
- destination path (`to`)
- optional exclusions (`exclude`)

A typical workflow is:

1. User defines components in `.git-components.yml`
2. Tool resolves each component to an exact commit
3. Tool writes `.git-components.lock`
4. Tool materializes imported files into the working tree
5. Tool adds imported folders to `.gitignore`
6. User commits the manifest and lock file

## Design goals

- Reproducible imports
- Human-editable configuration
- Partial import of repositories
- Clear separation of desired state and resolved state
- Predictable CLI behavior

## Non-goals

The following are out of scope for this tool:

- bidirectional synchronization
- preserving Git history of imported files
- automatic conflict merging between local edits and upstream content
- dependency graph resolution between components
- remote registry or package index support

## Required files

The tool recognizes the following files in the repository root:

- `.git-components.yml`
- `.git-components.lock`

## Exit code conventions

(as per `04-cli.md`)

### Success

- `0` = success

### General errors

- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `3`: Git failure
- `4`: any other filesystem error
- `5`: the given regex/glob pattern is not valid
- `6`: the specified command was unknown
- `7`: files were modified locally since last pull, and `--force` is not used
- `8`: unexpected usage of option `--filter-glob/filter-re/exclude-glob/exclude-re pattern`

### Reserved

- `9`: reserved
- `10`: reserved
  
### Component errors

- `11`: component is already present, and `--force` is not used
- `12`: component does not exist, and `--silent` is not used

### Reserved

- `13`: reserved
- `14`: reserved
 
### Manifest errors

- `15`: manifest and lock disagree, and `--update-lock` is not used
- `16`: manifest already exists, and `--force` is not used
- `17`: the manifest does nott exist or is not initialized
- `18`: the manifest exists but could not be read
- `19`: the manifest exists but could nott be edited
- `20`: the manifest could not be created

### Lock errors

- `21`: the lock does not exist or is invalid
- `22`: the lock exists but can not be read