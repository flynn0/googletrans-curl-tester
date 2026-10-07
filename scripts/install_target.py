#!/usr/bin/env python
"""Install the package under test (googletrans-curl) into the current interpreter.

The tester needs exactly one target distribution installed: either the
pre-release code from GitHub ("googletrans") or the published PyPI package
("googletrans-curl"). This script uninstalls both names first so switching
sources never leaves a stale copy behind.

Modes:
  git          install from https://github.com/kreier/googletrans-curl
               (default branch, or --ref <branch|tag|sha>)
  local PATH   install from a local checkout (test fixes before pushing)
  wheel PATH   install a built wheel (test the exact artifact before upload)
  pypi         install googletrans-curl from PyPI (--version required)
  show         report which target distribution is currently installed

Examples:
  python scripts/install_target.py git
  python scripts/install_target.py git --ref main
  python scripts/install_target.py local ../googletrans-curl
  python scripts/install_target.py wheel dist/googletrans_curl-4.0.3-py3-none-any.whl
  python scripts/install_target.py pypi --version 4.0.3
"""

import argparse
import importlib.metadata as importlib_metadata
import subprocess
import sys
from pathlib import Path

GIT_URL = "https://github.com/kreier/googletrans-curl.git"
TARGET_DISTRIBUTIONS = ("googletrans-curl", "googletrans")

PROBE = (
    "import importlib.metadata as m\n"
    "for name in ('googletrans-curl', 'googletrans'):\n"
    "    try:\n"
    "        print(f'  {name} {m.version(name)}')\n"
    "    except m.PackageNotFoundError:\n"
    "        pass\n"
)


def installed_targets():
    found = []
    for name in TARGET_DISTRIBUTIONS:
        try:
            found.append((name, importlib_metadata.version(name)))
        except importlib_metadata.PackageNotFoundError:
            continue
    return found


def run_pip(*args):
    cmd = [sys.executable, "-m", "pip", *args]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def show_installed():
    # Probe in a fresh interpreter so metadata reflects an install that
    # happened moments ago in this process.
    subprocess.run([sys.executable, "-c", PROBE], check=True)


def target_spec(args):
    if args.mode == "git":
        ref = f"@{args.ref}" if args.ref else ""
        return f"git+{GIT_URL}{ref}"
    if args.mode == "pypi":
        return f"googletrans-curl=={args.version}"
    if args.mode == "local":
        path = Path(args.path).resolve()
        if not (path / "pyproject.toml").is_file() and not (path / "setup.py").is_file():
            raise SystemExit(f"error: {path} does not look like a Python package checkout")
        return str(path)
    if args.mode == "wheel":
        path = Path(args.path).resolve()
        if not path.is_file() or path.suffix != ".whl":
            raise SystemExit(f"error: {path} is not a wheel file")
        return str(path)
    raise SystemExit(f"error: unknown mode {args.mode!r}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Install the package under test into the current interpreter.",
    )
    parser.add_argument(
        "--allow-system",
        action="store_true",
        help="allow running against a non-virtualenv interpreter (e.g. in CI)",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    git = subparsers.add_parser("git", help="install from the GitHub fork")
    git.add_argument("--ref", default=None, help="branch, tag or commit (default: default branch)")

    pypi = subparsers.add_parser("pypi", help="install googletrans-curl from PyPI")
    pypi.add_argument("--version", required=True, help="version to install, e.g. 4.0.3")

    local = subparsers.add_parser("local", help="install from a local checkout")
    local.add_argument("path", help="path to the googletrans-curl checkout")

    wheel = subparsers.add_parser("wheel", help="install a built wheel")
    wheel.add_argument("path", help="path to the .whl file")

    subparsers.add_parser("show", help="report the installed target version")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.mode == "show":
        print("Target distributions installed in", sys.prefix)
        show_installed()
        return 0

    if not args.allow_system and sys.prefix == sys.base_prefix:
        print(
            "error: refusing to modify a system-wide interpreter.\n"
            "Create and use a virtualenv first:\n"
            "  python -m venv .venv\n"
            "  .venv/Scripts/python scripts/install_target.py " + args.mode + " (Windows)\n"
            "  .venv/bin/python scripts/install_target.py " + args.mode + " (POSIX)\n"
            "Pass --allow-system to override (CI does this).",
            file=sys.stderr,
        )
        return 2

    spec = target_spec(args)

    run_pip("uninstall", "-y", *TARGET_DISTRIBUTIONS)
    run_pip("install", spec)

    print("\nInstalled target:", flush=True)
    show_installed()
    print("\nNext step: python -m pytest --offline", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\nerror: '{exc.cmd[-1]}' failed with exit code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)
