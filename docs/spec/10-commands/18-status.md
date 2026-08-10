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

The command reports up to four kinds of findings, each derived from step 2 above:

- `commit-changed`: a component's `branch`/`tag` now resolves to a different commit than the one recorded in the lock's `commit`.
- `resolve-error`: resolving a component's `branch`/`tag`/`commit` failed (e.g. the remote was unreachable).
- `pending-prune`: a component is present in the lock but no longer in the manifest (see `17-prune.md`).
- one of `modified` / `deleted` / `replaced-by-directory`: a file recorded in a component's `imported-files` no longer matches its recorded hash, is missing, or has been replaced by a directory (see "File change detection" in `03-lock-format.md`).

The exit code **shall** be `0` regardless of findings — this command reports state, it does not diff-check it.

### Default (human-readable) output

Findings **shall** be grouped into sections, in this order: `Commit updates available:`, `Errors resolving commit:`, `Pending prune (removed from the manifest, still present in the lock/filesystem):`, `Local modifications:`. A section **shall** be omitted entirely when it has no findings. Commit hashes in this section **shall** be abbreviated to their first 7 characters for readability. If there are no findings of any kind, the command **shall** print `up to date` instead of any section.

Example:

```
Commit updates available:
  mylib	a1b2c3d..f4e5d6c

Pending prune (removed from the manifest, still present in the lock/filesystem):
  oldlib

Local modifications:
  modified	mylib	vendor/mylib/core/a.py
```

### `--short` output

One line per finding, first whitespace-separated token identifying the kind, followed by the component name and any further fields; nothing is printed at all if there are no findings. Commit hashes in this format **shall** be the full (untruncated) hash, so the output stays unambiguous for scripts:

```
commit-changed <component> <old-commit> <new-commit>
resolve-error <component> <message>
pending-prune <component>
modified <component> <path>
deleted <component> <path>
replaced-by-directory <component> <path>
```

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
- `4`: any other filesystem error
- `17`: the manifest does not exist or is not initialized
- `18`: the manifest exists but could not be read, or its content is invalid