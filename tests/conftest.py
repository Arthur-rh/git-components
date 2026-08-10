import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def run_git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _commit(cwd, message):
    run_git(cwd, "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway destination git repository, cwd'd into, for CLI-level tests."""
    run_git(tmp_path, "init", "-q")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def source_repo(tmp_path_factory):
    """A local "remote" repository used as a component source in tests.

    Layout at the `main` tip:
      README.md
      src/core/a.py
      src/core/b.md
      src/core/e.py     (added in a 2nd commit, after the `v1.0` tag)
      src/utils/c.txt
      src/utils/tests/d.txt
    """
    src = tmp_path_factory.mktemp("source-repo")
    run_git(src, "init", "-q")
    write_file(src / "README.md", "hello\n")
    write_file(src / "src" / "core" / "a.py", "print('a')\n")
    write_file(src / "src" / "core" / "b.md", "# b\n")
    write_file(src / "src" / "utils" / "c.txt", "c\n")
    write_file(src / "src" / "utils" / "tests" / "d.txt", "d\n")
    run_git(src, "add", "-A")
    _commit(src, "initial")
    run_git(src, "branch", "-M", "main")
    run_git(src, "tag", "v1.0")

    write_file(src / "src" / "core" / "e.py", "print('e')\n")
    run_git(src, "add", "-A")
    _commit(src, "add e.py")

    return src


@pytest.fixture
def source_repo_b(tmp_path_factory):
    """A second, unrelated local "remote" repository, for cross-component conflict tests."""
    src = tmp_path_factory.mktemp("source-repo-b")
    run_git(src, "init", "-q")
    write_file(src / "other.txt", "other\n")
    run_git(src, "add", "-A")
    _commit(src, "initial")
    run_git(src, "branch", "-M", "main")
    return src
