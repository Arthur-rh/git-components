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

**From source, via pip** (recommended — not yet published to the public PyPI index):

```bash
pip install .
```

This installs the `gitcomponent` package and puts a `git-component` executable on your `PATH` via the `[project.scripts]` entry point in `pyproject.toml` — which is exactly what lets Git find it and makes `git component ...` work as a real Git subcommand, alongside direct `git-component ...` invocation.

**Standalone binary** (no Python required on the target machine):

```bash
pip install -r requirements-dev.txt
make build   # produces dist/git-component via PyInstaller
```

Put the resulting `git-component` (`git-component.exe` on Windows) on your `PATH`.

**For local development**, without installing anything onto `PATH`:

```bash
pip install -r requirements-dev.txt
python src/main.py <subcommand> [options]
```

**Building distributable artifacts** (sdist + wheel, e.g. to hand to someone else or eventually publish):

```bash
make dist            # produces dist/*.tar.gz and dist/*.whl
make publish-check   # validates them with `twine check` (no upload)
```

Actually publishing (`twine upload dist/*`) is a deliberate, one-way action and is intentionally not automated — run it yourself when ready.

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

`pull`/`resolve` still shell out to `git ls-remote` for commit resolution on every invocation (cheap, no object transfer), but checkout now uses a local mirror cache under `.git/git-components-cache/` (one per distinct `repository-url`, updated with `git fetch` rather than a fresh full clone each time) — see `docs/spec/10-commands/16-pull.md`.

`status`'s output format was marked `***TBD***` in the spec; it's now decided and documented in `docs/spec/10-commands/18-status.md`.

`order` is explicitly **not** part of v1 (see [`docs/spec/10-commands/20-order.md`](docs/spec/10-commands/20-order.md)) and is deferred to a later release.

## Contributing
[`docs/spec/`](docs/spec/) is the source of truth for behavior — implementation changes that diverge from it should update the spec first. `docs/spec/validate-error-codes.md` cross-checks exit-code documentation consistency across the spec files; run it after editing exit codes.

## Releasing

`main` is where development happens; `release` only ever holds commits that have been deliberately promoted from `main`. Tagging a commit on `release` triggers `.gitlab-ci.yml`, which runs the test suite, builds the package, then — in parallel — publishes to PyPI, creates a GitLab Release, and pushes that same commit (as `main`) plus the tag to the public GitHub mirror.

To cut a release:

```bash
# 1. bump the version on main
#    edit `version = "..."` in pyproject.toml, commit, push

# 2. fast-forward release to main
git checkout release
git merge --ff-only main
git push origin release

# 3. tag it (must match pyproject.toml's version, with a `v` prefix) and push the tag
git tag vX.Y.Z
git push origin vX.Y.Z
```

Pushing the tag is what triggers the pipeline — nothing publishes just from pushing to `release`.

The pipeline depends on three GitLab CI/CD variables (Settings → CI/CD → Variables), configured on the project already except where noted:
- `PYPI_PUBLISH_TOKEN` (masked, protected) — a PyPI API token. For the very first release, this must be an account-scoped token, since the project won't exist on PyPI yet to scope a token to.
- `GITHUB_MIRROR_URL` — the SSH URL of the public GitHub mirror (`git@github.com:owner/repo.git`).
- `GITHUB_DEPLOY_TOKEN` (masked, protected) — an SSH deploy key (with write access) for the GitHub mirror, stored as GitLab requires: without its `-----BEGIN/END-----` markers and with internal line breaks stripped, since masked variables must be a single line with no whitespace. The pipeline reconstructs a normal OpenSSH private key from it.

## Authors and acknowledgment
Arthur Richelet

## License
[Apache License 2.0](LICENSE)

## Project status
Specification complete for v1. All nine v1 subcommands are implemented and covered by an automated test suite (`make test`); see Roadmap for known gaps.
