"""Helpers shared by the test modules.

The public Google Translate endpoint occasionally answers with transient
errors, so online calls go through call_with_retry(). Console-script checks
locate the 'translate' script next to the running interpreter.
"""

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path


async def call_with_retry(operation, attempts=3, delay=2.0):
    """Await operation() and retry transient network errors a few times."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 - any transport error is worth a retry
            last_error = exc
            if attempt < attempts:
                await asyncio.sleep(delay)
    raise last_error


def find_console_script(name):
    """Locate a console script next to the running interpreter, then on PATH."""
    suffix = ".exe" if os.name == "nt" else ""
    candidate = Path(sys.executable).with_name(name + suffix)
    if candidate.is_file():
        return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def run_console_script(script, args, timeout=90):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )
