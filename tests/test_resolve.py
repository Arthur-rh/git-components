import yaml

from gitcomponent import errors
from gitcomponent.cli import main


def test_resolve_writes_lock_without_pulling_files(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])

    assert main(["resolve"]) == errors.EXIT_SUCCESS

    assert not (repo / "vendor").exists()
    data = yaml.safe_load((repo / ".git-components.lock").read_text())
    entry = data["components"]["mylib"]
    assert entry["resolved-from"] == {"branch": "main"}
    assert entry["imported-files"] == {}
    assert len(entry["commit"]) == 40


def test_resolve_then_pull_reuses_resolved_commit(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])
    main(["resolve"])

    before = yaml.safe_load((repo / ".git-components.lock").read_text())
    assert main(["pull"]) == errors.EXIT_SUCCESS
    after = yaml.safe_load((repo / ".git-components.lock").read_text())

    assert before["components"]["mylib"]["commit"] == after["components"]["mylib"]["commit"]
    assert (repo / "vendor/mylib/core/a.py").exists()


def test_resolve_unknown_component_fails(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "a:b"])
    assert main(["resolve", "nope"]) == errors.EXIT_COMPONENT_NOT_FOUND


def test_resolve_without_manifest_fails(repo):
    assert main(["resolve"]) == errors.EXIT_MANIFEST_MISSING
