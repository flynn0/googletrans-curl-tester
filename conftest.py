"""Root pytest options, kept separate from tests/conftest.py on purpose.

pytest registers options from conftest files it discovers while parsing the
command line, before collection. A value like `--report-file
dashboard/public/results.json` where the file already exists is mistaken for
a test path, so tests/conftest.py would not be loaded and the options would
be rejected as unrecognized. The rootdir conftest.py is always loaded first.
"""

import pytest


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
    parser.addoption(
        "--report-file",
        action="store",
        default=None,
        metavar="PATH",
        help="write a JSON report of the run (feeds the dashboard) to PATH",
    )
