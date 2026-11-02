# googletrans-curl-tester

[![tests](https://github.com/flynn0/googletrans-curl-tester/actions/workflows/test.yml/badge.svg)](https://github.com/flynn0/googletrans-curl-tester/actions/workflows/test.yml)
[![pages](https://github.com/flynn0/googletrans-curl-tester/actions/workflows/pages.yml/badge.svg)](https://github.com/flynn0/googletrans-curl-tester/actions/workflows/pages.yml)
[![Latest Release](https://img.shields.io/github/v/release/flynn0/googletrans-curl-tester?color=blue)](https://github.com/flynn0/googletrans-curl-tester/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Release-gate test harness for the [googletrans-curl](https://github.com/kreier/googletrans-curl)
PyPI package - a fork of [py-googletrans](https://github.com/ssut/py-googletrans).

The fork is published on PyPI as [googletrans-curl](https://pypi.org/project/googletrans-curl/)
**4.1.0**. The import name remains `googletrans`; the API supports both async
(`await Translator().translate(...)`) and synchronous workflows
(`SyncTranslator().translate(...)` or `Translator().translate_sync(...)`).

**Live test report: https://flynn0.github.io/googletrans-curl-tester/** -
summary cards per outcome plus expandable per-test details (source, markers,
failure output), regenerated on every push to main and nightly.

## Quickstart

```bash
python -m venv .venv

# On POSIX (Linux / macOS):
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python scripts/install_target.py pypi --version 4.1.0
.venv/bin/python -m pytest

# On Windows:
.venv\Scripts\python -m pip install -r requirements-test.txt
.venv\Scripts\python scripts/install_target.py pypi --version 4.1.0
.venv\Scripts\python -m pytest
```

Alternatively, activate the virtual environment first (`source .venv/bin/activate` on POSIX or `.venv\Scripts\activate` on Windows), and run `python scripts/install_target.py ...` and `pytest` directly.

## What the suite covers

| Area | File | Network |
| --- | --- | --- |
| installed distribution + version gate | tests/test_packaging.py | no |
| imports, language tables, models, input validation | tests/test_api_offline.py | no |
| translations (en/de, batch, non-latin, round trip) | tests/test_translate_online.py | yes |
| language detection | tests/test_detect_online.py | yes |
| `translate` console script | tests/test_cli.py | partly |

Useful invocations:

```bash
python -m pytest --offline                  # skip network tests
python -m pytest -m online                  # only network tests
python -m pytest --expected-version 4.1.0   # release gate
```

## Current status (verified against the published PyPI package 4.1.0)

- `googletrans-curl 4.1.0` installs and imports cleanly; async and sync translations,
  language detection, and CLI work cleanly across the full suite
- both async (`Translator`) and sync (`SyncTranslator`, `Translator.translate_sync`, `Translator.detect_sync`) APIs are tested

## Installing different sources of the package

| Goal | Command |
| --- | --- |
| current git main | `python scripts/install_target.py git` |
| local checkout (test fixes before pushing) | `python scripts/install_target.py local ../googletrans-curl` |
| built wheel (pre-upload check) | `python scripts/install_target.py wheel dist/googletrans_curl-4.1.0-py3-none-any.whl` |
| published package | `python scripts/install_target.py pypi --version 4.1.0` |
| show what is installed | `python scripts/install_target.py show` |

## CI

- push / pull request: offline suite on Ubuntu + Windows, Python 3.9 and 3.13,
  against the fork's git main
- nightly + manual: full online suite against the published PyPI release
  (manual runs accept an optional version gate input)
- push to main / nightly: the full suite runs against the published PyPI
  release, is rendered into the test dashboard and deployed to GitHub Pages

## Test dashboard

`dashboard/` is a small Vite app (vanilla JS, no framework) that renders a
pytest run as a web page with dynamic dark and light mode theme support (featuring
a one-click header toggle, `localStorage` persistence, and OS color scheme detection).
Generate its data with:

```bash
python -m pytest --report-file dashboard/public/results.json
cd dashboard && npm install && npm run build   # output in dashboard/dist/
```

The [pages workflow](.github/workflows/pages.yml) does this automatically and
publishes the result to https://flynn0.github.io/googletrans-curl-tester/.

See [AGENTS.md](AGENTS.md) for the agent-oriented workflow, test conventions
and the 4.1.0 release checklist.
