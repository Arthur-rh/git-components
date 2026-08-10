import pytest

from gitcomponent import errors, manifest


def test_default_manifest():
    assert manifest.default_manifest() == {"version": 1, "components": {}}


def test_validate_rejects_missing_version():
    with pytest.raises(errors.ManifestInvalidError):
        manifest.validate({"components": {}})


def test_validate_rejects_multiple_selectors():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "branch": "main",
                "tag": "v1",
                "imports": [{"from": "src/", "to": "vendor/"}],
            }
        },
    }
    with pytest.raises(errors.ManifestInvalidError):
        manifest.validate(data)


def test_validate_rejects_missing_selector():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "imports": [{"from": "src/", "to": "vendor/"}],
            }
        },
    }
    with pytest.raises(errors.ManifestInvalidError):
        manifest.validate(data)


def test_validate_rejects_absolute_path():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "branch": "main",
                "imports": [{"from": "/etc/passwd", "to": "vendor/"}],
            }
        },
    }
    with pytest.raises(errors.ManifestInvalidError):
        manifest.validate(data)


def test_validate_rejects_invalid_regex():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "branch": "main",
                "imports": [{"from": "src/", "to": "vendor/", "filter-re": ["("]}],
            }
        },
    }
    with pytest.raises(errors.InvalidPatternError):
        manifest.validate(data)


def test_validate_accepts_minimal_valid_manifest():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "branch": "main",
                "imports": [{"from": "src/", "to": "vendor/"}],
            }
        },
    }
    assert manifest.validate(data) == []


def test_validate_warns_on_unknown_field():
    data = {
        "version": 1,
        "components": {
            "foo": {
                "repository-url": "https://example.com/foo.git",
                "branch": "main",
                "imports": [{"from": "src/", "to": "vendor/"}],
                "bogus-field": True,
            }
        },
    }
    warnings = manifest.validate(data)
    assert any("bogus-field" in w for w in warnings)


def test_component_name_allows_single_character():
    assert manifest.COMPONENT_NAME_RE.match("a")
    assert manifest.COMPONENT_NAME_RE.match("_")
