"""Cross-component conflict handling (see "Conflict handling" in docs/spec/10-commands/16-pull.md)."""
import yaml

from gitcomponent import errors
from gitcomponent.cli import main


def test_higher_priority_component_wins_conflict(repo, source_repo, source_repo_b):
    main(["init"])
    main(["add", "first", str(source_repo), "branch=main", "--map", "src/core/a.py:shared/a.py"])
    main(["add", "second", str(source_repo_b), "branch=main", "--map", "other.txt:shared/a.py"])

    assert main(["pull"]) == errors.EXIT_SUCCESS

    assert (repo / "shared/a.py").read_text() == "print('a')\n"  # from `first`, higher priority

    lock_data = yaml.safe_load((repo / ".git-components.lock").read_text())
    assert "shared/a.py" in lock_data["components"]["first"]["imported-files"]
    assert "shared/a.py" not in lock_data["components"]["second"].get("imported-files", {})
    assert lock_data["components"]["second"]["suppressed-files"]["shared/a.py"] == "first@src/core/a.py:shared/a.py"


def test_partial_pull_overwrite_by_higher_priority_later(repo, source_repo, source_repo_b):
    main(["init"])
    main(["add", "first", str(source_repo), "branch=main", "--map", "src/core/a.py:shared/a.py"])
    main(["add", "second", str(source_repo_b), "branch=main", "--map", "other.txt:shared/a.py"])

    # partial pull: only the lower-priority component, which is free to claim the path
    assert main(["pull", "second"]) == errors.EXIT_SUCCESS
    assert (repo / "shared/a.py").read_text() == "other\n"

    # full pull: `first` outranks `second` and shall reclaim shared/a.py
    assert main(["pull"]) == errors.EXIT_SUCCESS
    assert (repo / "shared/a.py").read_text() == "print('a')\n"

    lock_data = yaml.safe_load((repo / ".git-components.lock").read_text())
    assert "shared/a.py" in lock_data["components"]["first"]["imported-files"]
    assert "shared/a.py" not in lock_data["components"]["second"].get("imported-files", {})
    assert lock_data["components"]["second"]["suppressed-files"]["shared/a.py"] == "first@src/core/a.py:shared/a.py"


def test_lower_priority_partial_pull_does_not_overwrite_existing_owner(repo, source_repo, source_repo_b):
    main(["init"])
    main(["add", "first", str(source_repo), "branch=main", "--map", "src/core/a.py:shared/a.py"])
    main(["add", "second", str(source_repo_b), "branch=main", "--map", "other.txt:shared/a.py"])

    assert main(["pull", "first"]) == errors.EXIT_SUCCESS
    assert main(["pull", "second"]) == errors.EXIT_SUCCESS

    assert (repo / "shared/a.py").read_text() == "print('a')\n"  # untouched by the lower-priority pull
