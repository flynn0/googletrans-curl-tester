"""Offline tests for test run tracking and history database."""

import json
from pathlib import Path

from scripts.update_history import add_pytest_report, load_history, recompute_summary

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = REPO_ROOT / "dashboard" / "public" / "history.json"


def test_history_file_exists_and_is_valid():
    assert HISTORY_PATH.exists(), "dashboard/public/history.json must exist"
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    assert "runs" in data
    assert "summary" in data
    assert len(data["runs"]) >= 70, "History database should contain historical runs since Oct 7"


def test_history_starts_from_october_7():
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    first_run = data["summary"]["first_run"]
    assert first_run is not None
    assert first_run.startswith("2026-10-07"), f"Expected first run on 2026-10-07, got {first_run}"


def test_history_summary_consistency():
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    runs = data["runs"]
    summary = data["summary"]

    assert summary["total_runs"] == len(runs)
    expected_success = sum(1 for r in runs if r.get("conclusion") == "success")
    assert summary["successful_runs"] == expected_success
    assert 0 <= summary["success_rate"] <= 100.0


def test_run_records_have_required_fields():
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    required_keys = {"id", "workflow", "status", "conclusion", "created_at"}
    for run in data["runs"]:
        missing = required_keys - set(run.keys())
        assert not missing, f"Run {run.get('id')} missing keys: {missing}"


def test_add_pytest_report_and_recompute_summary(tmp_path):
    history_file = tmp_path / "history.json"
    data = load_history(history_file)
    assert data["summary"]["total_runs"] == 0

    fake_report = tmp_path / "report.json"
    fake_report.write_text(
        json.dumps({
            "generated_at": "2026-11-02T12:00:00Z",
            "mode": "offline",
            "exit_status": 0,
            "duration": 1.23,
            "environment": {"git": {"commit": "abcdef1", "branch": "test"}},
            "summary": {"total": 10, "passed": 10, "failed": 0, "skipped": 0, "xfailed": 0, "xpassed": 0, "errors": 0},
        }),
        encoding="utf-8",
    )

    added = add_pytest_report(data, fake_report)
    assert added is True
    assert data["summary"]["total_runs"] == 1
    assert data["summary"]["successful_runs"] == 1
    assert data["summary"]["success_rate"] == 100.0
