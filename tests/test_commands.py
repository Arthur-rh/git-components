import yaml

from gitcomponent import errors
from gitcomponent.cli import main


def test_init_creates_manifest(repo):
    assert main(["init"]) == errors.EXIT_SUCCESS
    manifest_file = repo / ".git-components.yml"
    assert manifest_file.exists()
    assert yaml.safe_load(manifest_file.read_text()) == {"version": 1, "components": {}}


def test_init_refuses_to_overwrite_without_force(repo):
    assert main(["init"]) == errors.EXIT_SUCCESS
    assert main(["init"]) == errors.EXIT_MANIFEST_ALREADY_EXISTS


def test_init_force_overwrites(repo):
    assert main(["init"]) == errors.EXIT_SUCCESS
    assert main(["init", "--force"]) == errors.EXIT_SUCCESS


def test_init_outside_git_repo_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == errors.EXIT_NOT_GIT_REPO


def test_add_then_list(repo, capsys):
    main(["init"])
    exit_code = main(
        ["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "src/:vendor/mylib/src/"]
    )
    assert exit_code == errors.EXIT_SUCCESS

    capsys.readouterr()
    assert main(["list"]) == errors.EXIT_SUCCESS
    out = capsys.readouterr().out
    assert "mylib" in out
    assert "branch=main" in out


def test_add_with_filters(repo):
    main(["init"])
    exit_code = main(
        [
            "add", "mylib", "https://example.com/mylib.git", "branch=main",
            "--map", "src/:vendor/mylib/src/",
            "--exclude-glob", "**/*.md",
            "--exclude-glob", "tests/**",
        ]
    )
    assert exit_code == errors.EXIT_SUCCESS

    manifest_file = repo / ".git-components.yml"
    data = yaml.safe_load(manifest_file.read_text())
    rule = data["components"]["mylib"]["imports"][0]
    assert rule["exclude-glob"] == ["**/*.md", "tests/**"]


def test_add_rejects_filter_without_preceding_map(repo):
    main(["init"])
    exit_code = main(
        ["add", "mylib", "https://example.com/mylib.git", "branch=main", "--filter-glob", "*.txt"]
    )
    assert exit_code == errors.EXIT_UNEXPECTED_FILTER_OPTION


def test_add_rejects_invalid_regex(repo):
    main(["init"])
    exit_code = main(
        ["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "a:b", "--filter-re", "("]
    )
    assert exit_code == errors.EXIT_INVALID_PATTERN


def test_add_rejects_duplicate_without_force(repo):
    main(["init"])
    main(["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "a:b"])
    exit_code = main(["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "a:b"])
    assert exit_code == errors.EXIT_COMPONENT_ALREADY_PRESENT


def test_add_force_overwrites(repo):
    main(["init"])
    main(["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "a:b"])
    exit_code = main(
        ["add", "mylib", "https://example.com/mylib.git", "tag=v1", "--map", "a:b", "--force"]
    )
    assert exit_code == errors.EXIT_SUCCESS


def test_remove_then_list_silent(repo):
    main(["init"])
    main(["add", "mylib", "https://example.com/mylib.git", "branch=main", "--map", "a:b"])
    assert main(["remove", "mylib"]) == errors.EXIT_SUCCESS
    assert main(["list", "mylib"]) == errors.EXIT_COMPONENT_NOT_FOUND
    assert main(["list", "mylib", "--silent"]) == errors.EXIT_SUCCESS


def test_remove_unknown_component_fails(repo):
    main(["init"])
    assert main(["remove", "nope"]) == errors.EXIT_COMPONENT_NOT_FOUND
    assert main(["remove", "nope", "--silent"]) == errors.EXIT_SUCCESS


def test_list_without_manifest_fails(repo):
    assert main(["list"]) == errors.EXIT_MANIFEST_MISSING


def test_help_unknown_command(repo):
    assert main(["help", "bogus"]) == errors.EXIT_UNKNOWN_COMMAND


def test_help_known_command(repo, capsys):
    assert main(["help", "add"]) == errors.EXIT_SUCCESS
    assert "add" in capsys.readouterr().out


def test_pull_not_yet_implemented(repo):
    main(["init"])
    from gitcomponent.commands.pull import EXIT_NOT_IMPLEMENTED

    assert main(["pull"]) == EXIT_NOT_IMPLEMENTED
