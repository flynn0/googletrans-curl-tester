# googletrans-curl-tester

Release-gate test harness for the [googletrans-curl](https://github.com/kreier/googletrans-curl)
PyPI package - a fork of [py-googletrans](https://github.com/ssut/py-googletrans).

The fork is published on PyPI as [googletrans-curl](https://pypi.org/project/googletrans-curl/)
**4.0.3**. The import name remains `googletrans`; since 4.0 the API is async
(`await Translator().translate(...)`).

**Live test report: https://flynn0.github.io/googletrans-curl-tester/** -
summary cards per outcome plus expandable per-test details (source, markers,
failure output), regenerated on every push to main and nightly.

## Quickstart

```bash
python -m venv .venv
# Windows
.venv/Scripts/python -m pip install -r requirements-test.txt
.venv/Scripts/python scripts/install_target.py pypi --version 4.0.3
.venv/Scripts/python -m pytest
# POSIX: replace .venv/Scripts with .venv/bin
```

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
python -m pytest --expected-version 4.0.3   # release gate
```

## Current status (verified 2026-10-08 against the published PyPI package)

- `googletrans-curl 4.0.3` installs and imports cleanly; real translations and
  language detection work - the full suite is **24 passed**
- both pre-release defects are fixed, so their `xfail(strict=True)` markers are
  gone: `googletrans.__version__` now matches the distribution metadata, and
  the `translate` console script runs (`--help` and a real translation)

## Installing different sources of the package

| Goal | Command |
| --- | --- |
| current git main | `python scripts/install_target.py git` |
| local checkout (test fixes before pushing) | `python scripts/install_target.py local ../googletrans-curl` |
| built wheel (pre-upload check) | `python scripts/install_target.py wheel dist/googletrans_curl-4.0.3-py3-none-any.whl` |
| published package | `python scripts/install_target.py pypi --version 4.0.3` |
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
pytest run as a web page. Generate its data with:

```bash
python -m pytest --report-file dashboard/public/results.json
cd dashboard && npm install && npm run build   # output in dashboard/dist/
```

The [pages workflow](.github/workflows/pages.yml) does this automatically and
publishes the result to https://flynn0.github.io/googletrans-curl-tester/.

See [AGENTS.md](AGENTS.md) for the agent-oriented workflow, test conventions
and the 4.0.3 release checklist.
