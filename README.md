# git-component

## Description
This project's goal is to add a new command to Git enabling the use of "component(s)". They resemble Git submodules and subtrees but with differentiating characteristics:

- submodules:
  - cannot reference tags, while components can do
  - pull the whole repository, components can select which files or directories to pull
- subtrees:
  - **shall** merge histories, components are ignored by git and are in read-only by default to avoid unwanted modifications

See [`docs/spec/`](docs/spec/) for the full specification: manifest and lock file formats, CLI behavior, and per-subcommand semantics.

## Installation

Requires Python 3.8+.

```bash
pip install -r requirements-dev.txt
make build   # produces dist/git-component via PyInstaller
```

Put the resulting `git-component` (`git-component.exe` on Windows) on your `PATH` so it can be invoked both as `git-component ...` and as `git component ...`.

For local development without building a binary:

```bash
pip install -r requirements-dev.txt
python src/main.py <subcommand> [options]
```

## Usage

```bash
git component init
git component add <name> <repo_url> branch=<branch> --map <src>:<dest>
git component list [--all] [components...]
git component remove <components...>
git component pull [components...]
git component prune [components...]
git component status [--short]
git component resolve [components...]
git component help [command]
```

Full per-subcommand synopses and semantics live in [`docs/spec/10-commands/`](docs/spec/10-commands/).

## Support
Open an issue in this repository describing the problem, including the manifest/lock content involved and the exact command run.

## Roadmap
v1 subcommands (per [`docs/spec/04-cli.md`](docs/spec/04-cli.md)): `help`, `init`, `add`, `remove`, `pull`, `prune`, `list`, `status`, `resolve`. All nine are implemented, including cross-component/partial-pull priority conflict resolution, `.gitignore` management, and local-modification detection.

Known gaps, worth tracking as follow-ups:
- `status`'s output format is marked `***TBD***` in the spec itself (`docs/spec/10-commands/18-status.md`); the format implemented here is a placeholder pending an authoritative decision.
- `pull`/`resolve` shell out to `git ls-remote`/`git clone` per invocation, with no local object-database caching, so repeated pulls of the same component re-clone it from scratch.

`order` is explicitly **not** part of v1 (see [`docs/spec/10-commands/20-order.md`](docs/spec/10-commands/20-order.md)) and is deferred to a later release.

## Contributing
[`docs/spec/`](docs/spec/) is the source of truth for behavior — implementation changes that diverge from it should update the spec first. `docs/spec/validate-error-codes.md` cross-checks exit-code documentation consistency across the spec files; run it after editing exit codes.

## Authors and acknowledgment
Arthur Richelet

## License
***TBD***

## Project status
Specification complete for v1. All nine v1 subcommands are implemented and covered by an automated test suite (`make test`); see Roadmap for known gaps.
