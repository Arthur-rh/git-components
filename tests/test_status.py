import os

from conftest import run_git
from gitcomponent import errors
from gitcomponent.cli import main


def _setup_pulled_component(repo, source_repo, ref="branch=main"):
    main(["init"])
    main(["add", "mylib", str(source_repo), ref, "--map", "src/core/:vendor/mylib/core/"])
    main(["pull"])


def test_status_up_to_date(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)
    capsys.readouterr()

    assert main(["status"]) == errors.EXIT_SUCCESS
    assert "up to date" in capsys.readouterr().out


def test_status_reports_pending_prune(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])
    capsys.readouterr()

    assert main(["status"]) == errors.EXIT_SUCCESS
    assert "mylib" in capsys.readouterr().out


def test_status_reports_commit_drift(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)  # branch=main
    capsys.readouterr()

    # upstream moves forward after we pulled/locked
    (source_repo / "src" / "core" / "f.py").write_text("print('f')\n")
    run_git(source_repo, "add", "-A")
    run_git(source_repo, "-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "add f.py")

    assert main(["status"]) == errors.EXIT_SUCCESS
    out = capsys.readouterr().out
    assert "mylib" in out
    assert "commit updates" in out.lower()


def test_status_reports_local_modification(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)

    path = repo / "vendor/mylib/core/a.py"
    os.chmod(path, 0o644)
    path.write_text("tampered\n")
    capsys.readouterr()

    assert main(["status"]) == errors.EXIT_SUCCESS
    assert "modified" in capsys.readouterr().out


def test_status_short_format_reports_pending_prune(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)
    main(["remove", "mylib"])
    capsys.readouterr()

    main(["status", "--short"])
    assert "pending-prune mylib" in capsys.readouterr().out


def test_status_short_format_commit_changed_includes_both_hashes(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)  # branch=main
    capsys.readouterr()

    (source_repo / "src" / "core" / "f.py").write_text("print('f')\n")
    run_git(source_repo, "add", "-A")
    run_git(source_repo, "-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "add f.py")

    main(["status", "--short"])
    lines = capsys.readouterr().out.splitlines()
    matching = [line for line in lines if line.startswith("commit-changed ")]
    assert len(matching) == 1

    kind, name, old, new = matching[0].split()
    assert (kind, name) == ("commit-changed", "mylib")
    assert len(old) == 40 and len(new) == 40
    assert old != new


def test_status_up_to_date_short_format_prints_nothing(repo, source_repo, capsys):
    _setup_pulled_component(repo, source_repo)
    capsys.readouterr()

    main(["status", "--short"])
    assert capsys.readouterr().out == ""


def test_status_without_lock(repo, source_repo):
    main(["init"])
    main(["add", "mylib", str(source_repo), "branch=main", "--map", "a:b"])
    assert main(["status"]) == errors.EXIT_SUCCESS


def test_status_without_manifest_fails(repo):
    assert main(["status"]) == errors.EXIT_MANIFEST_MISSING
