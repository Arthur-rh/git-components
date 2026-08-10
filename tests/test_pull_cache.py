"""Local mirror cache used by `pull`/`resolve` checkouts (see gitcomponent/remote.py)."""
from conftest import rev_parse, run_git
from gitcomponent import errors
from gitcomponent.cli import main


def test_pull_creates_a_local_mirror_cache(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])
    assert main(["pull"]) == errors.EXIT_SUCCESS

    cache_root = repo / ".git" / "git-components-cache"
    assert cache_root.is_dir()
    entries = list(cache_root.iterdir())
    assert len(entries) == 1
    assert (entries[0] / "HEAD").exists()  # looks like a bare/mirror repo


def test_pull_reuses_cache_on_second_pull(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])
    main(["pull"])

    cache_root = repo / ".git" / "git-components-cache"
    before = {p: p.stat().st_mtime for p in cache_root.rglob("*")}

    assert main(["pull"]) == errors.EXIT_SUCCESS
    assert (repo / "vendor/mylib/core/a.py").exists()

    # the mirror directory itself shouldn't have been recreated (same files, same mtimes)
    after = {p: p.stat().st_mtime for p in cache_root.rglob("*")}
    assert set(before) == set(after)


def test_pull_fetches_cache_when_upstream_gains_a_commit(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "src/core/:vendor/mylib/core/"])
    main(["pull"])  # warms the cache at the current tip
    assert (repo / "vendor/mylib/core/e.py").exists()

    run_git(source_repo, "rm", "-q", "src/core/e.py")
    run_git(source_repo, "-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "drop e.py")

    # the new tip isn't in the cache yet; pull shall fetch it rather than fail
    assert main(["pull", "--update-lock"]) == errors.EXIT_SUCCESS
    assert not (repo / "vendor/mylib/core/e.py").exists()


def test_pull_with_commit_selector_uses_cache(repo, source_repo):
    commit = rev_parse(source_repo)

    main(["init"])
    main(["add", "mylib", str(source_repo), f"commit={commit}", "--map", "src/core/:vendor/mylib/core/"])
    assert main(["pull"]) == errors.EXIT_SUCCESS
    assert (repo / "vendor/mylib/core/a.py").read_text() == "print('a')\n"


def test_pull_caches_two_components_from_the_same_repo_separately_per_url(repo, source_repo, source_repo_b):
    main(["init"])
    main(["add", "first", str(source_repo), "branch=main", "--map", "src/core/a.py:a.py"])
    main(["add", "second", str(source_repo_b), "branch=main", "--map", "other.txt:other.txt"])
    assert main(["pull"]) == errors.EXIT_SUCCESS

    cache_root = repo / ".git" / "git-components-cache"
    assert len(list(cache_root.iterdir())) == 2
    assert (repo / "a.py").exists()
    assert (repo / "other.txt").exists()
