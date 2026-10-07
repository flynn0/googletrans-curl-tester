# AGENTS.md

Agent guide for the googletrans-curl tester repository.

## What this repository is

A release-gate test harness for the **googletrans-curl** PyPI package.

| Fact | Value |
| --- | --- |
| Package under test | https://github.com/kreier/googletrans-curl (fork of https://github.com/ssut/py-googletrans) |
| PyPI project name | `googletrans-curl` (not published yet; target release **4.0.3**) |
| Import name | `googletrans` |
| API style | async since 4.0: `await Translator().translate(...)` |
| Runtime dependency | `httpx[http2]` as of the 4.0.2 code base |
| This repo | pure test harness - never fix package bugs here, fix them in the fork |

Functional tests talk to the real Google Translate endpoint (marker:
`online`). Packaging metadata, imports, language tables, and input validation
are covered offline.

## Layout

```
conftest.py                 pytest options only (rootdir: always parsed first)
tests/
  conftest.py               fixtures + JSON report hooks (--report-file)
  helpers.py                retry helper, console-script helpers, xfail reasons
  test_packaging.py         installed distribution metadata / version gate
  test_api_offline.py       imports, constants, models, invalid-input errors
  test_translate_online.py  real translations (network)
  test_detect_online.py     real language detection (network)
  test_cli.py               'translate' console script
scripts/install_target.py   installs the package under test (git/local/wheel/pypi)
dashboard/                  Vite app that renders a pytest report as a web page
  src/                      main.js + style.css (no framework)
  public/results.json       report data consumed by the app
.github/workflows/test.yml  CI: offline on push/PR, online nightly + manual
.github/workflows/pages.yml CI: test, build dashboard, deploy to GitHub Pages
```

## Environment setup (fresh clone)

```bash
python -m venv .venv
# Windows:
.venv/Scripts/python -m pip install -r requirements-test.txt
.venv/Scripts/python scripts/install_target.py git
# POSIX:
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python scripts/install_target.py git
```

Run pytest with the venv interpreter (`.venv/Scripts/python -m pytest` on
Windows, `.venv/bin/python -m pytest` on POSIX) from the repository root.
The suite refuses to start with a clear message if the target is not
installed.

## Commands

| Goal | Command |
| --- | --- |
| Full suite incl. network | `python -m pytest` |
| Offline only | `python -m pytest --offline` |
| Network only | `python -m pytest -m online` |
| Release gate | `python -m pytest --expected-version 4.0.3` |
| Write dashboard data | `python -m pytest --report-file dashboard/public/results.json` |
| Dashboard dev server | `cd dashboard && npm install && npm run dev` |
| Test the built dashboard | `cd dashboard && npm run build && npm run preview` |
| Show installed target | `python scripts/install_target.py show` |
| Test a local fix | `python scripts/install_target.py local ../googletrans-curl` |
| Test a built wheel | `python scripts/install_target.py wheel dist/googletrans_curl-4.0.3-py3-none-any.whl` |
| Post-release check | `python scripts/install_target.py pypi --version 4.0.3` |

## How the package under test is installed

pyproject.toml deliberately does NOT declare the target as a dependency: the
distribution name changes from `googletrans` (git checkout) to
`googletrans-curl` (PyPI), which breaks pip direct-URL name checks and can
leave a stale copy under the other name. Always install through
scripts/install_target.py - it uninstalls both names first and refuses to
modify system interpreters without `--allow-system`.

Tests accept either distribution name but fail when BOTH are installed
(tests/test_packaging.py::test_exactly_one_target_distribution_installed).

## Test conventions

- async tests need no decorator: pytest-asyncio runs in `auto` mode.
- any test touching the network MUST carry the `online` marker; offline runs
  (`--offline`) must stay green without network access.
- use the `translator` fixture and `helpers.call_with_retry` for online calls.
- assert stable substrings only (e.g. `"hallo" in result.text.lower()`);
  exact machine-translation output is never stable across time and locale.
- do not assert on transport internals (httpx specifics) - the 4.0.3 release
  may switch the HTTP layer (the "curl" in the name).
- conftest.py must not import googletrans at module level; the fixture
  imports it lazily so pytest_configure can raise a friendly UsageError when
  the target is missing.
- command-line options live in the rootdir conftest.py, not tests/conftest.py:
  pytest registers options from conftests it discovers while parsing argv, and
  a value like an existing `--report-file` path makes pytest skip
  tests/conftest.py entirely, rejecting the options. The rootdir conftest is
  always read first.

## Test dashboard (GitHub Pages)

https://flynn0.github.io/googletrans-curl-tester/ hosts `dashboard/`, a Vite
app (vanilla JS, no framework) showing the latest test run: summary cards per
outcome, a section per test module, and expandable rows with each test's
source, markers, and failure output.

Data flow: conftest.py writes a JSON report via `--report-file`; the app
fetches `<base>/results.json` at runtime. The file lives in
dashboard/public/results.json so Vite copies it into the build.

`.github/workflows/pages.yml` regenerates the report on every push to main
(and nightly): it runs the full suite with `continue-on-error` - failures are
the point of a test dashboard, they must not block the deploy - then builds
and deploys `dashboard/dist` via actions/deploy-pages. Pages is configured
with build type "workflow" in the repository settings; there is no gh-pages
branch.

Notes for changes to the dashboard:
- the app must keep working from the `/googletrans-curl-tester/` base path
  (vite.config.js `base`, `import.meta.env.BASE_URL` for the fetch URL).
- do not rename dashboard/ to site/ - .gitignore has `/site` from the Python
  template.
- results.json is data, not an artifact: commit the latest snapshot.

## Known pre-release issues (tracked as xfail(strict=True))

Both exist in the upstream 4.0.2 code base and should be fixed in the fork
before publishing 4.0.3:

1. `googletrans.__version__` is stale (`"3.4.0"`) while the distribution
   metadata says 4.0.2
   (tests/test_packaging.py::test_module_version_matches_distribution)
2. the `translate` console script crashes with ImportError: the declared
   entry point `translate = "googletrans:translate"` targets an attribute the
   package does not export (tests/test_cli.py, both tests)

Do not delete or weaken these tests. After the fork is fixed they report
XPASS(strict) and the suite goes red on purpose: remove the xfail marker at
that point to lock the fix in.

## Release gate for 4.0.3

1. Fix the two tracked defects in the fork; bump the fork to 4.0.3 (and to
   the `googletrans-curl` distribution name if that is the publishing plan).
2. `python scripts/install_target.py local <checkout>` then
   `python -m pytest --offline` for a fast signal.
3. Remove the xfail markers (the tests will XPASS after the fixes).
4. `python -m pytest --expected-version 4.0.3` - everything must be green.
5. Build the wheel, `python scripts/install_target.py wheel <wheel>`, rerun
   the full online suite against the exact artifact.
6. Publish, then `python scripts/install_target.py pypi --version 4.0.3` and
   run the full suite once more against the published package.
