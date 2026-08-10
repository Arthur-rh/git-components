import os

from gitcomponent import errors
from gitcomponent.cli import main


def _setup_pulled_component(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])
    main(["pull"])


def test_prune_removes_obsolete_component_files(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    assert (repo / "vendor/mylib/core/a.py").exists()

    main(["remove", "mylib"])
    assert main(["prune"]) == errors.EXIT_SUCCESS
    assert not (repo / "vendor/mylib/core/a.py").exists()


def test_prune_removes_now_empty_directories(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])
    main(["prune"])

    assert not (repo / "vendor").exists()


def test_prune_removes_gitignore_entries(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])
    main(["prune"])

    gitignore = (repo / ".gitignore").read_text() if (repo / ".gitignore").exists() else ""
    assert "mylib" not in gitignore


def test_prune_nothing_to_do(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    assert main(["prune"]) == errors.EXIT_SUCCESS
    assert (repo / "vendor/mylib/core/a.py").exists()  # nothing obsolete, nothing removed


def test_prune_without_lock_fails(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "a:b"])
    assert main(["prune"]) == errors.EXIT_LOCK_MISSING_OR_INVALID


def test_prune_unknown_component_fails(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])
    assert main(["prune", "nope"]) == errors.EXIT_COMPONENT_NOT_FOUND


def test_prune_refuses_local_modifications_without_force(repo, source_repo):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])

    path = repo / "vendor/mylib/core/a.py"
    os.chmod(path, 0o644)
    path.write_text("tampered\n")

    assert main(["prune"]) == errors.EXIT_LOCAL_MODIFICATIONS
    assert main(["prune", "--force"]) == errors.EXIT_SUCCESS
