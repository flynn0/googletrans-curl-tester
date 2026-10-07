"""The 'translate' console script declared in the package's pyproject.toml.

Both runtime checks are xfail(strict=True): they document a known defect of
the 4.0.2 code base that should be fixed in the fork before the 4.0.3
release. When they start reporting XPASS, delete the markers - do not weaken
the assertions.
"""

import pytest

from helpers import CLI_XFAIL_REASON, find_console_script, run_console_script


def test_entry_point_is_declared(target_distribution):
    names = [
        entry_point.name
        for entry_point in target_distribution.entry_points
        if entry_point.group == "console_scripts"
    ]
    assert "translate" in names


@pytest.mark.xfail(strict=True, reason=CLI_XFAIL_REASON)
def test_translate_cli_help():
    script = find_console_script("translate")
    assert script is not None, "console script 'translate' is not installed"
    proc = run_console_script(script, ["--help"])
    assert proc.returncode == 0, proc.stderr
    assert "usage" in proc.stdout.lower()


@pytest.mark.online
@pytest.mark.xfail(strict=True, reason=CLI_XFAIL_REASON)
def test_translate_cli_translates():
    script = find_console_script("translate")
    assert script is not None, "console script 'translate' is not installed"
    proc = run_console_script(script, ["Hello world", "-d", "de"])
    assert proc.returncode == 0, proc.stderr
    assert "hallo" in proc.stdout.lower()
