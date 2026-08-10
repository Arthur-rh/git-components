# Manifest Format Specification

## File

`.git-components.yml`

## Purpose

The manifest defines the desired set of external components and how their contents **shall** be imported into the current repository.

## Top-level structure

The manifest file **shall** be a YAML mapping with the following structure:

```yaml
version: 1

components:
  <component-name>:
    repository-url: <git-url>
    branch: <branch-name> | optional
    tag: <tag-name> | optional
    commit: <commit-id> | optional
    imports:
      - from: <source-path>
        to: <destination-path>
        filter-re:
          - <pattern>
        filter-glob:
          - <pattern>
        # both filter-re and filter-glob can exist simultaneously and **shall** be combined as "filter-re OR filter-glob"
        exclude-re:
          - <pattern>
        exclude-glob:
          - <pattern>
        # both exclude-re and exclude-glob can exist simultaneously and **shall** be combined as "exclude_or OR exclude-glob"
    add-to-gitignore: <yaml boolean> | defaults to true
```

## Top-level fields

### `version`
- Required
- Integer
- Current supported value: `1`

### `components`
- Required
- Mapping from component name to component definition
- **shall** not be empty for commands that operate on components

## Component definition

Each component definition **shall** be a YAML mapping.
The component name **shall** match `[A-Za-z_][A-Za-z0-9_-]+`

### Required fields

#### `repository-url`
- Required
- String
- Git repository URL or transport string accepted by Git

#### `imports`
- Required
- Non-empty list of import rule objects

### Revision selector fields

Exactly one of the following **shall** be specified:

- `branch`
- `tag`
- `commit`

#### `branch`
- Optional
- String
- Indicates a branch name to resolve to the latest reachable commit

#### `tag`
- Optional
- String
- Indicates a tag name to resolve
- The implementation **shall** support lightweight tags.

#### `commit`
- Optional
- String
- Indicates an exact commit to use directly

### Revision selector rules

A component:
- **may** define `branch`, `tag`, or `commit`
- **shall** define exactly one of them
- **shall** be considered invalid if more than one is present

If none is present, the manifest is invalid.

## Import rule structure

Each entry in `imports` **shall** be a mapping with the following fields:

### `from` (source)
- Required
- String
- Path inside the source repository
- **May** refer to a directory or file
- Interpreted relative to the repository root

### `to` (destination)
- Required
- String
- Destination path inside the current repository
- **May** refer to a directory or file
- Interpreted relative to the destination repository root

### `filter_*`
- Optional
- Can be `filter-glob` or `filter-re`
- List of regex strings or glob strings
- The tool applies the rules relative to the root of the repository
- The tool applies the rules after the mapping
- The tool combines the rules with an `OR` operator
- If no `filter-*` rules are specified, the tool **shall** include all files (subject to exclude rules).

### `exclude_*`
- Optional
- Can be `exclude-glob` or `exclude-re`
- List of regex strings or glob strings
- Each string is a pattern used to filter out files within the imported content
- The tool applies the rules relative to the root of the repository
- The tool applies the rules after the mapping
- The tool combines the rules with an `OR` operator
- If no `exclude-*` rules are specified, the tool **shall** not exclude any files.

## Path rules

### `from`
- **shall** not be absolute
- **shall** not escape the source repository root
- **Shall** use forward-slash style separators in the manifest
- Trailing slash **may** be accepted for readability but **shall** not change semantic meaning beyond indicating a directory intent

### `to`
- **shall** not be absolute
- **shall** not escape the destination repository root
- **Shall** use forward-slash style separators in the manifest

## File/folder mapping

- `from` is the `source` of files
- `to` is the `destination` of files

- if the `source` is a *directory*, its contents **shall** be copied to the `destination` path,
  - if the `destination` path is an **already existing file**, it **shall** return an error `a directory can not be copied inside a file`.
- if the `source` is a *file*, it **shall** be copied to the `destination` path,
  - if the `destination` path is an **already existing directory**, it **shall** copy the file into the directory.
  - **IMPORTANT NOTE**: using this behavior is discouraged as it can lead to inconsistant imports: if the directory does not exists beforehand, the file **shall** be copied as a file and **shall** take the name of its intended target directory.

## Filter and exclude semantics

- Exclude/filter patterns are evaluated to all files concerned by their corresponding mapping.
- Only files that match the filter **shall** be copied.
- Excluded files **shall** not be copied.
- Patterns are either:
  - `glob` patterns when used in `filter-glob` or `exclude-glob`
  - `regex (python 3.6 re)` patterns when used in `filter-re` or `exclude-re`.
- When adding a component, the regex pattern **shall** be valid, if not the command returns an error.

Example:

```yaml
imports:
  - from: src/
    to: vendor/lib/src/
    filter-re:
      - .*\d{2}-\d{2}-\d{2}.* # only include files that contain a date in format DD-MM-YY
    exclude-glob:
      - **/*.md # exclude markdown files
```

This means matching files under the imported `src/` content are skipped.

## Component naming rules

Component names:
- are keys under `components`
- **shall** be unique
- **shall** consist of simple ASCII identifiers suitable for CLI display
- **shall** avoid whitespace
- **shall** be treated as case-sensitive unless implementation documentation states otherwise

### Priority order

#### Between components

- The top most component in the file **shall** have the highest priority, then in a descending order from the manifest/lock.
- If two component aim to import two separate files as source into the same destination file, the first component in the file **shall** have the priority, the next components to be imported **shall** not overwrite the files previously imported by a higher priority component.

#### Between file mappings of a given component

- The top most file mapping rule in a component **shall** have the higest priority, then in a descending order from the manifest.
- If two rules aim to import two separate files as source into the same destination file, the first rule in the component **shall** have the priority, the next rules to be imported **shall** not overwrite the files previously imported by a higher priority rule.

## Example

```yaml
version: 1

components:
  mylib:
    repository-url: https://github.com/example/mylib.git
    branch: main
    imports:
      - from: include/
        to: third_party/mylib/include/
      - from: src/core/
        to: third_party/mylib/src/core/
        exclude-glob:
          - tests/**
          - "**/*.md"
    add-to-gitignore: yes

  utils:
    repository-url: https://github.com/example/utils.git
    tag: v2.1.0
    imports:
      - from: lib/
        to: vendor/utils/
        filter-glob:
          - .*\.txt
    add-to-gitignore: yes
```

## Validation requirements

The manifest **shall** be rejected if:

- the YAML is syntactically invalid
- `version` is missing or unsupported
- `components` is missing or not a mapping
- a component name does not match correct format
- a component lacks `repository-url`
- a component lacks `imports`
- a component defines zero import rules
- a component defines more than one selector among `branch`, `tag`, `commit`
- a component defines none of `branch`, `tag`, `commit`
- an import rule lacks `from` or `to`
- a path is absolute or escapes repository root semantics
- `exclude-glob/exclude-re/filter-glob/filter-re` is present but is not a list of strings
- `add-to-gitignore` is not in a boolean format (see : [Boolean Language-Independent Type for YAMLÖ Version 1.1 - tag:yaml.org,2002:bool](https://yaml.org/type/bool.html)) 

## Unknown fields

- unknown top-level fields **shall** cause a validation warning
- unknown component fields **shall** cause a validation warning
- unknown import-rule fields **shall** cause a validation warning