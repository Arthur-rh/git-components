import pytest

from gitcomponent import errors, lock


def test_default_lock():
    assert lock.default_lock() == {"version": 1, "components": {}}


def test_validate_accepts_minimal_valid_lock():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "commit": "a" * 40,
                "resolved-from": {"branch": "main"},
                "imported-files": {},
            }
        },
    }
    lock.validate(data)  # shall not raise


def test_validate_rejects_missing_commit():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "resolved-from": {"branch": "main"},
                "imported-files": {},
            }
        },
    }
    with pytest.raises(errors.LockMissingOrInvalidError):
        lock.validate(data)


def test_validate_rejects_ambiguous_resolved_from():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "commit": "a" * 40,
                "resolved-from": {"branch": "main", "tag": "v1"},
                "imported-files": {},
            }
        },
    }
    with pytest.raises(errors.LockMissingOrInvalidError):
        lock.validate(data)
