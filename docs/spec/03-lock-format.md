# Lock Format Specification

## Purpose

The lock records the exact resolved commit for each component so imports can be reproduced consistently.

## File

- The lock file is by default named `.git-components.lock`.
- The tool places the manifest file at the root of the repository by default. 
- Using the option `--lock <lock_file>` allows to specify a different lock file to use.

## Top-level structure

The lock file **shall** be a YAML mapping with the following structure:

```yaml
version: 1

components:
  <component-name>:
    repository-url: <git-url>
    commit: <full-commit-id>
    resolved-from:
      branch: <branch-name>
      # or
      tag: <tag-name>
      # or
      commit: <commit-id>
      # exactly one **shall** be present
    imported-files:
      <filepath>: <file_hash>
      <filepath>: <file_hash>
    suppressed-files:
      <filepath>: <component>@<from>:<to> # from and to are from the rule

```

## Top-level fields

### `version`
- Required
- Integer
- Current supported value: `1`

### `components`
- Required
- Mapping from component name to locked component definition
- The document order of keys under `components` **shall** match the priority order defined by the manifest (see *Priority order* in `02-manifest-format.md`), since `pull` processes components "in top-bottom order in the lock" (see `10-commands/16-pull.md`). Implementations **shall** parse and represent this mapping using an order-preserving structure.

## Locked component definition

Each locked component **shall** contain:

### `repository-url`
- Required
- String
- Repository URL or Git transport string

### `commit`
- Required
- String
- Exact resolved commit hash
- Full hash is recommended

### `resolved-from`
- Required
- Mapping
- Records the selector intent from the manifest resolution

Examples:

```yaml
resolved-from:
  branch: main
```

```yaml
resolved-from:
  tag: v2.1.0
```

```yaml
resolved-from:
  commit: a1b2c3...
```

### `imported-files`

- Lists all files that have been imported and their hash at the time of importation.
```yaml
imported-files:
      path/to/file1.txt: a1b2c3d4e5f678901234567890abcdef12345678
      path/to/file2.txt: 901234567890abcdef12345678d4e5f678904d6a
```

### `suppressed-files`

- Lists all files that should have been imported but were already imported by a higher priority component.
- Stores who successfully imported the file as a value.
- **shall** be a plain mapping from `<filepath>` to `<component>@<from>:<to>`, matching the top-level structure shown above (not a YAML list).
```yaml
suppressed-files:
      path/to/file2.txt: mylib@lib/path:path/to/file # because mylib already imports file2.txt in this path and has priority
```

## Relationship to manifest

The tool **shall** derive the lock from the manifest

The lock normally does not duplicate:
- `imports`
- `exclude`
- destination mappings

Those remain authoritative in `.git-components.yml`.

## Consistency expectations

If both manifest and lock exist:

- component names in the lock **shall** correspond to component names in the manifest
- `repository-url` in the lock **shall** match the manifest `repository-url`
- `resolved-from` **shall** match the selector type and value in the manifest
- `commit` **shall** be the exact revision used for synchronization

If manifest and lock disagree, commands **shall** either:
- report drift and refuse to proceed, or
- notice the user of the drift
- refresh the lock when the subcommand explicitly permits it

## File change detection

The command **shall** store the `SHA-1` hash of the content of each file in the lock to detect any modification made locally before calling `pull` and `prune`.
If a file is missing, it **shall** count as modified (deleted),
If a directory replaces a file, it **shall** count as modified (deleted)

## Example

```yaml
version: 1

components:
  mylib:
    repository-url: https://github.com/example/mylib.git
    commit: a1b2c3d4e5f678901234567890abcdef12345678
    resolved-from:
      branch: main
    imported-files:
      path/to/file1.txt: a1b2c3d4e5f678901234567890abcdef12345678
      path/to/file2.txt: 901234567890abcdef12345678d4e5f678904d6a

  utils:
    repository-url: https://github.com/example/utils.git
    commit: f0e1d2c3b4a5968778695a4b3c2d1e0f12345678
    resolved-from:
      tag: v2.1.0
    imported-files:
      path/to/file3.txt: c3d4e5f67890123bcdef1234563d4e5f3467890a
    suppressed-files: 
      path/to/file2.txt: mylib@lib/path:path/to/file # putting this on a single line makes it easier to grep
```

## Validation requirements

The lock **shall** be rejected if:

- YAML is syntactically invalid
- `version` is missing or unsupported
- `components` is missing or not a mapping
- a locked component is missing `repository-url`
- a locked component is missing `commit`
- a locked component is missing `resolved-from`
- a locked component is missing `imported-files`
- `resolved-from` does not contain exactly one of `branch`, `tag`, `commit`

## Missing lock file

Some commands **may** operate without an existing lock by generating it.

The absence of `.git-components.lock` is not always an error.
It depends on the subcommand.
