"""Distribution-level checks: what exactly is installed, and does it match the release plan?"""

import pytest
from packaging.version import Version

import googletrans

# Oldest version this suite is known to describe correctly.
MINIMUM_SUPPORTED = Version("4.0.2")


def test_exactly_one_target_distribution_installed(target_distributions):
    assert len(target_distributions) == 1, (
        "both 'googletrans' and 'googletrans-curl' are installed; tests would be "
        "ambiguous about which module gets imported (a stale copy of the other "
        "name shadows the real target)."
    )


def test_distribution_version_within_supported_range(target_version):
    assert target_version >= MINIMUM_SUPPORTED, (
        f"installed target version {target_version} is older than "
        f"{MINIMUM_SUPPORTED}; the test suite does not describe it"
    )


def test_version_matches_expected_version(target_version, expected_version):
    if expected_version is None:
        pytest.skip("pass --expected-version X.Y.Z to enforce a specific version")
    assert target_version == expected_version


def test_module_is_importable():
    assert callable(googletrans.Translator)
    assert "Translator" in googletrans.__all__


@pytest.mark.xfail(
    strict=True,
    reason=(
        "googletrans.__version__ is '3.4.0' in the 4.0.2 code base while the "
        "distribution metadata says 4.0.2; expected to be fixed in googletrans-curl "
        "4.0.3 - remove this xfail marker once __version__ matches the metadata."
    ),
)
def test_module_version_matches_distribution(target_distribution):
    assert googletrans.__version__ == target_distribution.version
