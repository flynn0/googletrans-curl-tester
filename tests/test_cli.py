"""The 'translate' console script declared in the package's pyproject.toml."""

import pytest

from helpers import find_console_script, run_console_script


def test_entry_point_is_declared(target_distribution):
    names = [
        entry_point.name
        for entry_point in target_distribution.entry_points
        if entry_point.group == "console_scripts"
    ]
    assert "translate" in names


def test_translate_cli_help():
    script = find_console_script("translate")
    assert script is not None, "console script 'translate' is not installed"
    proc = run_console_script(script, ["--help"])
    assert proc.returncode == 0, proc.stderr
    assert "usage" in proc.stdout.lower()


@pytest.mark.online
def test_translate_cli_translates():
    script = find_console_script("translate")
    assert script is not None, "console script 'translate' is not installed"
    proc = run_console_script(script, ["Hello world", "-d", "de"])
    assert proc.returncode == 0, proc.stderr
    assert "hallo" in proc.stdout.lower()
