from sift_core import __version__, package_name


def test_package_name_when_imported() -> None:
    assert package_name() == "sift-core"


def test_version_is_semver_placeholder() -> None:
    assert __version__ == "0.0.0"
