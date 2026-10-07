"""Fixtures and options shared by the googletrans-curl pre-release test suite.

Run with --offline to skip network tests, and with --expected-version X.Y.Z
as a release gate (fails unless the installed target reports that version).
"""

import importlib.metadata as importlib_metadata
import sys

import pytest
from packaging.version import InvalidVersion, Version

TARGET_DISTRIBUTIONS = ("googletrans-curl", "googletrans")


def find_target_distributions():
    found = []
    for name in TARGET_DISTRIBUTIONS:
        try:
            found.append(importlib_metadata.distribution(name))
        except importlib_metadata.PackageNotFoundError:
            continue
    return found


def pytest_configure(config):
    if not find_target_distributions():
        raise pytest.UsageError(
            "the package under test is not installed (looked for "
            f"{' and '.join(TARGET_DISTRIBUTIONS)} in {sys.prefix}); "
            "install it first with: python scripts/install_target.py git"
        )


def pytest_addoption(parser):
    parser.addoption(
        "--offline",
        action="store_true",
        default=False,
        help="skip all tests marked 'online' (no network access)",
    )
    parser.addoption(
        "--expected-version",
        action="store",
        default=None,
        metavar="VERSION",
        help=(
            "fail unless the installed target reports exactly VERSION; "
            "use as a release gate, e.g. --expected-version 4.0.3"
        ),
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--offline"):
        skip_online = pytest.mark.skip(reason="--offline: test needs network access")
        for item in items:
            if "online" in item.keywords:
                item.add_marker(skip_online)


@pytest.fixture(scope="session")
def target_distributions():
    return find_target_distributions()


@pytest.fixture(scope="session")
def target_distribution(target_distributions):
    if len(target_distributions) != 1:
        found = [dist.metadata["Name"] for dist in target_distributions]
        pytest.fail(
            f"expected exactly one of {TARGET_DISTRIBUTIONS} to be installed, "
            f"found {found}; clean up both names and reinstall via "
            "scripts/install_target.py"
        )
    return target_distributions[0]


@pytest.fixture(scope="session")
def target_version(target_distribution):
    return Version(target_distribution.version)


@pytest.fixture
def expected_version(request):
    raw = request.config.getoption("--expected-version")
    if raw is None:
        return None
    try:
        return Version(raw)
    except InvalidVersion:
        pytest.fail(f"--expected-version {raw!r} is not a valid version")


@pytest.fixture
async def translator():
    from googletrans import Translator

    async with Translator() as instance:
        yield instance
