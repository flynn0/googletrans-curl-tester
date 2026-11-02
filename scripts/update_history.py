#!/usr/bin/env python3
"""Maintains the run history database (history.json) for googletrans-curl-tester.

Keeps track of historical and future test runs, both from GitHub Actions
workflows (tests, pages) and from local pytest reports.

Usage:
    python scripts/update_history.py --sync-gh
    python scripts/update_history.py --from-report dashboard/public/results.json
    python scripts/update_history.py --show
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

DEFAULT_HISTORY_PATH = Path("dashboard/public/history.json")
DEFAULT_ROOT_COPY = Path("history.json")


def load_history(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: could not read existing {path}: {e}", file=sys.stderr)
    return {
        "version": "1.0",
        "repository": "flynn0/googletrans-curl-tester",
        "last_updated": None,
        "summary": {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "success_rate": 0.0,
            "first_run": None,
            "latest_run": None,
        },
        "runs": [],
    }


def recompute_summary(data: dict) -> dict:
    runs = data.get("runs", [])
    # Sort chronologically (oldest first)
    runs.sort(key=lambda r: r.get("created_at") or "")

    total = len(runs)
    successes = sum(1 for r in runs if r.get("conclusion") == "success")
    failures = sum(1 for r in runs if r.get("conclusion") in ("failure", "timed_out", "cancelled"))

    data["summary"] = {
        "total_runs": total,
        "successful_runs": successes,
        "failed_runs": failures,
        "success_rate": round((successes / total) * 100, 1) if total > 0 else 0.0,
        "first_run": runs[0]["created_at"] if runs else None,
        "latest_run": runs[-1]["created_at"] if runs else None,
    }
    data["last_updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["runs"] = runs
    return data


def sync_from_github(data: dict, limit: int = 300) -> int:
    """Fetch recent and past runs using the GitHub CLI (gh)."""
    try:
        cmd = [
            "gh",
            "run",
            "list",
            "--limit",
            str(limit),
            "--json",
            "databaseId,name,workflowName,status,conclusion,event,createdAt,updatedAt,headSha,headBranch,url",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw_runs = json.loads(proc.stdout)
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Notice: unable to query GitHub Actions runs ({e})", file=sys.stderr)
        return 0

    existing_by_id = {str(r["id"]): r for r in data.get("runs", []) if "id" in r}
    added_or_updated = 0

    for r in raw_runs:
        db_id = str(r["databaseId"])
        created = r["createdAt"]
        updated = r.get("updatedAt") or created
        try:
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            u = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            dur = max(0, int((u - c).total_seconds()))
        except Exception:
            dur = 0

        record = {
            "id": db_id,
            "workflow": r.get("workflowName") or "tests",
            "name": r.get("name") or r.get("workflowName"),
            "event": r.get("event") or "push",
            "status": r.get("status") or "completed",
            "conclusion": r.get("conclusion") or "unknown",
            "created_at": created,
            "updated_at": updated,
            "duration": dur,
            "commit": (r.get("headSha") or "")[:7] or None,
            "branch": r.get("headBranch") or "main",
            "url": r.get("url") or f"https://github.com/flynn0/googletrans-curl-tester/actions/runs/{db_id}",
        }

        if db_id not in existing_by_id:
            data.setdefault("runs", []).append(record)
            existing_by_id[db_id] = record
            added_or_updated += 1
        else:
            # Update status/conclusion if changed
            existing = existing_by_id[db_id]
            if existing.get("conclusion") != record["conclusion"] or existing.get("status") != record["status"]:
                existing.update(record)
                added_or_updated += 1

    recompute_summary(data)
    return added_or_updated


def add_pytest_report(data: dict, report_path: Path) -> bool:
    """Import a pytest report JSON file (e.g. results.json) into the history."""
    if not report_path.exists():
        print(f"Error: report file {report_path} not found.", file=sys.stderr)
        return False

    with open(report_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    gen_at = rep.get("generated_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
    git = (rep.get("environment") or {}).get("git") or {}
    commit = git.get("commit") or "unknown"
    branch = git.get("branch") or "main"
    exit_status = rep.get("exit_status", 0)
    conclusion = "success" if exit_status == 0 else "failure"

    run_id = f"pytest-{commit}-{gen_at.replace(':', '').replace('-', '')}"
    existing_ids = {str(r.get("id")) for r in data.get("runs", [])}

    if run_id in existing_ids:
        print(f"Report run {run_id} is already in history.")
        return False

    summary = rep.get("summary") or {}
    targets = (rep.get("environment") or {}).get("targets") or []
    target_str = ", ".join(f"{t['distribution']} {t['version']}" for t in targets) if targets else ""

    record = {
        "id": run_id,
        "workflow": "local-pytest",
        "name": f"pytest ({rep.get('mode', 'full')})",
        "event": "manual",
        "status": "completed",
        "conclusion": conclusion,
        "created_at": gen_at,
        "updated_at": gen_at,
        "duration": round(rep.get("duration", 0), 1),
        "commit": commit[:7] if commit else None,
        "branch": branch,
        "url": None,
        "expected_version": rep.get("expected_version"),
        "target": target_str,
        "summary": {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0) + summary.get("errors", 0),
            "skipped": summary.get("skipped", 0),
            "xfailed": summary.get("xfailed", 0),
            "xpassed": summary.get("xpassed", 0),
        },
    }

    data.setdefault("runs", []).append(record)
    recompute_summary(data)
    return True


def save_history(data: dict, target_paths: list[Path]):
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    for path in target_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        print(f"Saved run history to {path}")


def main():
    parser = argparse.ArgumentParser(description="Update test run history database.")
    parser.add_argument(
        "--history-file",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help=f"Path to history JSON file (default: {DEFAULT_HISTORY_PATH})",
    )
    parser.add_argument(
        "--root-copy",
        type=Path,
        default=DEFAULT_ROOT_COPY,
        help=f"Copy to repository root path (default: {DEFAULT_ROOT_COPY})",
    )
    parser.add_argument(
        "--from-report",
        type=Path,
        default=None,
        help="Import a pytest results JSON file into history",
    )
    parser.add_argument(
        "--sync-gh",
        action="store_true",
        default=True,
        help="Sync workflow runs from GitHub Actions (default: True)",
    )
    parser.add_argument(
        "--no-sync-gh",
        dest="sync_gh",
        action="store_false",
        help="Skip syncing workflow runs from GitHub Actions",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print summary of recorded runs and exit",
    )

    args = parser.parse_args()

    data = load_history(args.history_file)

    if args.show:
        summary = data.get("summary", {})
        print(f"Total runs: {summary.get('total_runs', 0)}")
        print(f"Successful: {summary.get('successful_runs', 0)}")
        print(f"Failed:     {summary.get('failed_runs', 0)}")
        print(f"Success %:  {summary.get('success_rate', 0)}%")
        print(f"First run:  {summary.get('first_run')}")
        print(f"Latest run: {summary.get('latest_run')}")
        return

    changed = False

    if args.sync_gh:
        count = sync_from_github(data)
        if count > 0:
            changed = True
            print(f"Synced {count} run(s) from GitHub Actions.")

    if args.from_report:
        if add_pytest_report(data, args.from_report):
            changed = True
            print(f"Imported run from {args.from_report}.")

    # If data was loaded or newly populated, ensure summary is computed
    recompute_summary(data)
    save_targets = [args.history_file]
    if args.root_copy and args.root_copy != args.history_file:
        save_targets.append(args.root_copy)

    save_history(data, save_targets)


if __name__ == "__main__":
    main()
