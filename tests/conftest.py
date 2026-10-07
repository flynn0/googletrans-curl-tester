"""Fixtures and option handling shared by the googletrans-curl test suite.

Run with --offline to skip network tests, and with --expected-version X.Y.Z
as a release gate (fails unless the installed target reports that version).
Pass --report-file PATH to write a JSON run report (feeds the dashboard).

The command-line options themselves are declared in the root conftest.py so
they are registered before pytest parses arguments; see that file for why.
"""

import importlib.metadata as importlib_metadata
import inspect
import json
import platform
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

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


def pytest_collection_modifyitems(config, items):
    if config.getoption("--offline"):
        skip_online = pytest.mark.skip(reason="--offline: test needs network access")
        for item in items:
            if "online" in item.keywords:
                item.add_marker(skip_online)

    if not config.getoption("--report-file"):
        return
    for item in items:
        function = getattr(item, "function", None)
        source = None
        if function is not None:
            try:
                source = textwrap.dedent(inspect.getsource(function)).rstrip()
            except (OSError, TypeError):
                source = None
        _REPORT["tests"][item.nodeid] = {
            "nodeid": item.nodeid,
            "module": item.nodeid.split("::", 1)[0],
            "name": item.name,
            "markers": sorted({marker.name for marker in item.iter_markers()}),
            "source": source,
            "reports": {},
        }


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


# ---------------------------------------------------------------------------
# JSON run report for the dashboard (--report-file)
# ---------------------------------------------------------------------------

# The start time is captured here, at import: when an existing --report-file
# value is scanned as an initial path, this conftest is loaded during
# collection, after pytest_sessionstart has already fired.
_REPORT = {"started": time.time(), "tests": {}}


def _skip_reason(report):
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2])
    return None


def _longrepr_text(report, limit=5000):
    longrepr = getattr(report, "longrepr", None)
    if longrepr is None:
        return None
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2])
    text = str(longrepr)
    if len(text) > limit:
        text = text[:limit] + "\n... (truncated)"
    return text


def _git_info(root):
    def run(*args):
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()

    try:
        return {
            "commit": run("rev-parse", "--short", "HEAD"),
            "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        }
    except Exception:
        return None


def _finalize(reports):
    """Reduce phase reports to (outcome, reason, strict, detail, stdout)."""
    setup = reports.get("setup")
    call = reports.get("call")
    teardown = reports.get("teardown")

    if setup is not None and setup["outcome"] == "failed":
        return "errors", None, False, setup["longrepr"], setup["stdout"]
    if setup is not None and setup["outcome"] == "skipped":
        if setup["wasxfail"]:
            return "xfailed", setup["wasxfail"], False, None, setup["stdout"]
        return "skipped", setup["skip_reason"], False, None, setup["stdout"]
    if call is not None:
        wasxfail = call["wasxfail"]
        if wasxfail and call["outcome"] == "skipped":
            return "xfailed", wasxfail, False, None, call["stdout"]
        if wasxfail and call["outcome"] == "passed":
            return "xpassed", wasxfail, False, None, call["stdout"]
        if wasxfail and call["outcome"] == "failed":
            # strict xfail: an unexpected pass fails the run
            return "xpassed", wasxfail, True, call["longrepr"], call["stdout"]
        if call["outcome"] == "failed" and (call["longrepr"] or "").startswith(
            "[XPASS(strict)]"
        ):
            # pytest reports an unexpected pass under xfail(strict=True) as a
            # failure with this prefix and without setting wasxfail
            reason = call["longrepr"].split("]", 1)[1].strip() or None
            return "xpassed", reason, True, call["longrepr"], call["stdout"]
        if call["outcome"] == "passed":
            return "passed", None, False, None, call["stdout"]
        if call["outcome"] == "failed":
            return "failed", None, False, call["longrepr"], call["stdout"]
        if call["outcome"] == "skipped":
            return "skipped", call["skip_reason"], False, None, call["stdout"]
    if teardown is not None and teardown["outcome"] == "failed":
        return "errors", None, False, teardown["longrepr"], teardown["stdout"]
    return "unknown", None, False, None, None


def pytest_runtest_logreport(report):
    entry = _REPORT["tests"].get(report.nodeid)
    if entry is None:
        return
    record = {
        "outcome": report.outcome,
        "duration": report.duration,
        "wasxfail": getattr(report, "wasxfail", None),
        "longrepr": _longrepr_text(report) if report.failed else None,
        "skip_reason": _skip_reason(report) if report.skipped else None,
        "stdout": (getattr(report, "capstdout", "") or "")[:4000] or None,
    }
    entry["reports"][report.when] = record


def pytest_sessionfinish(session, exitstatus):
    report_file = session.config.getoption("--report-file")
    if not report_file:
        return

    finished = time.time()
    started = _REPORT["started"] or finished

    summary = {name: 0 for name in ("passed", "failed", "skipped", "xfailed", "xpassed", "errors")}
    modules = {}

    for entry in _REPORT["tests"].values():
        outcome, reason, strict, detail, stdout = _finalize(entry["reports"])
        summary[outcome] = summary.get(outcome, 0) + 1
        test = {
            "nodeid": entry["nodeid"],
            "name": entry["name"],
            "markers": entry["markers"],
            "source": entry["source"],
            "outcome": outcome,
            "duration": round(sum(r["duration"] for r in entry["reports"].values()), 3),
        }
        if reason:
            test["reason"] = reason
        if strict:
            test["strict"] = True
        if detail:
            test["detail"] = detail
        if stdout:
            test["stdout"] = stdout
        modules.setdefault(entry["module"], []).append(test)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "offline" if session.config.getoption("--offline") else "full",
        "expected_version": session.config.getoption("--expected-version"),
        "exit_status": int(exitstatus),
        "duration": round(finished - started, 3),
        "summary": {"total": len(_REPORT["tests"]), **summary},
        "environment": {
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()}",
            "pytest": pytest.__version__,
            "targets": [
                {"distribution": dist.metadata["Name"], "version": dist.version}
                for dist in find_target_distributions()
            ],
            "git": _git_info(str(session.config.rootpath)),
        },
        "modules": [{"name": name, "tests": tests} for name, tests in modules.items()],
    }

    path = Path(report_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
