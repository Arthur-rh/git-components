# Subcommand Specification: pull

## Synopsis

```bash
git component pull [--force] [--verbose] [--strict] [--update-lock] [components...]
```

## Purpose

Pull the files from the components to match the manifest/lock

## Inputs

- manifest file is required
- the tool generates `.git-components.lock`

### Arguments

- `components`: (optional) if specified, only pulls these components (separated by whitespace).

### Options

- `--manifest <manifest_file>`: specifies a manifest file to use, by default `.git-components.yml`
- `--lock <lock_file>`: specified a lock file to use, by default `.git-components.lock`
- `--force`: bypasses the local file modifications check, this **shall** overwrite all local modifications made since last pull
- `--verbose`: display additional information
- `--strict`: treat warnings as errors
- `--update-lock`: if lock and manifest disagree, regenerate lock
- `--ignore-manifest`: if lock and manifest disagree, use lock and ignore manifest

## Core behavior

The command **shall**:

1. Load and validate manifest (including regex/glob patterns).

2. If one or more component are specified, verify their existence in the manifest.

3. Resolve all commit hashes if branches/tags are used as reference.

4. If the lock file exists and `--force` is not used, check all files hashes, if there is a mismatch, exit with error `7` (see *File change detection* in `03-lock-format.md`).

5. Regenerate the lock if needed (see *Lock regeneration*)

6. For each component in top-bottom order in the lock:
   1. Obtain the source repository content for the resolved commit.
   2. Remove all files of the component (from the `imported-files` in the lock).
   3. Remove all current imported files from `.gitignore`
   4. Copy matching files into their specified path.
   5. Apply exclusions (remove patterned files).
   6. Set files to read-only.
   7. Add the list of imported files to the lock and their hash.
   8. Add all files to `.gitignore` if specified in the `add-to-gitignore` of the component is set to boolean `true`.

## Files deletion before pull

- Because of the files deletion (step 7.2) mechanic before the pull of new files, any files that were previously tracked by a rule that is now removed from the manifest **shall** not be kept.

## Commit resolution rules

1. if the lock file is invalid, consider it missing.
2. if the lock file is missing, resolve from manifest and write into the lock file.
3. resolve the commit from the manifest
4. check the resolved commit against the commit hash in the current lock.
5. if manifest and lock disagree, fail unless `--update-lock` is used.

## Conflict handling

### Priority rule

- The pull works on a priority basis, the first component to be imported is at the top of the manifest/lock (see *Priority order - Between Components* in `02-manifest-format.md`).
- If two rules of the same component each aim to import a file into the same path, the highest priority rule **shall** be kept, and the other one(s) discarded while emitting a warning (as per "Priority order - Between rules" `02-manifest-format.md`).

### Component pull conflict

- If two or more components import a file to the same destination path, the implementation **shall** keep the file from the component with the highest priority. The implementation ****shall** not** import the file from any lower-priority component. The implementation **shall** emit a warning. See **"Priority order - Between components"** in `02-manifest-format.md`.

- The implementation **shall** record the destination file in the `imported-files` entry of the highest-priority component.
  
- The implementation **shall** record the destination file in the `suppressed-files` entry of each lower-priority component. The implementation ****shall** not** record that file in the `imported-files` entry of those components.

### Partial pull case

- If the `[components...]` argument is used, the command **shall** call a partial pull, where only the specified components **shall** be imported.

#### Conflicts on a partial pull case

- A partial pull can import files from a lower-priority component that a complete pull would suppress. This can occur because the higher-priority component is not part of the partial pull.

- When a higher-priority component is imported later, the implementation **shall** compare its priority with the component that previously imported each destination file.

- If the higher-priority component imports a file to a destination path that is already occupied by a lower-priority component, the implementation **shall** overwrite the existing file. The implementation **shall** update the lock file to record the new state.

- If the existing file was imported by a component with equal or higher priority, the implementation ****shall** not** overwrite the file.

## Success conditions

The command succeeds if all selected components are imported successfully and the working tree matches the locked state.

## Failure conditions

The command **shall** fail if:
- The provided manifest does not exist or can not be read
- The manifest format is invalid (see `02-manifest-format.md`)
- If provided, the component does not exist in the manifest
- Any underlying `git` command fails
- Any other filesystem operation fails
- Manifest and lock resolved commit hashes diagree, and `--update-lock` is not used 
- A file from a component was modified locally since last pull (hash mismatch), and `--force` is not used.

## Exit codes

- `0`: success
- `1`: argument validation error
- `2`: the command is not running inside an existing git repository
- `3`: Git failure
- `4`: any other filesystem error
- `5`: the given regex/glob pattern is not valid
- `7`: files were modified locally since last pull, and `--force` is not used
- `15`: manifest and lock disagree, and neither `--update-lock` nor `--ignore-manifest` is not used