import "./style.css";

const DATA_URL = `${import.meta.env.BASE_URL}results.json`;

const OUTCOME_LABELS = {
  passed: "passed",
  failed: "failed",
  errors: "error",
  xpassed: "xpassed",
  xfailed: "xfailed",
  skipped: "skipped",
};

const OUTCOME_ORDER = ["passed", "failed", "errors", "xpassed", "xfailed", "skipped"];

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  node.append(...children.filter((child) => child !== null && child !== undefined));
  return node;
}

function fmtDuration(seconds) {
  if (typeof seconds !== "number") return "";
  if (seconds >= 10) return `${seconds.toFixed(1)}s`;
  if (seconds >= 1) return `${seconds.toFixed(2)}s`;
  if (seconds >= 0.001) return `${seconds.toFixed(3)}s`;
  return "<0.001s";
}

function badge(outcome) {
  return el("span", {
    class: `badge badge-${outcome}`,
    text: OUTCOME_LABELS[outcome] ?? outcome,
  });
}

function card(value, label, tone = "") {
  return el(
    "div",
    { class: `card ${tone}`.trim() },
    el("div", { class: "card-value", text: String(value) }),
    el("div", { class: "card-label", text: label }),
  );
}

function kv(key, value) {
  return el("div", { class: "kv" }, el("span", { class: "k", text: key }), value);
}

function block(label, text) {
  return el(
    "div",
    { class: "block" },
    el("span", { class: "k", text: label }),
    el("pre", { text }),
  );
}

function masthead(data, exit) {
  const env = data.environment ?? {};
  const git = env.git;
  const targets =
    (env.targets ?? []).map((t) => `${t.distribution} ${t.version}`).join(", ") ||
    "not installed";

  const meta = [
    ["mode", data.mode === "offline" ? "offline (no network)" : "full run (network)"],
    ["target", targets],
    data.expected_version ? ["version gate", data.expected_version] : null,
    ["python", env.python ?? "?"],
    ["pytest", env.pytest ?? "?"],
    ["platform", env.platform ?? "?"],
    git ? ["revision", `${git.branch} @ ${git.commit}`] : null,
    ["generated", data.generated_at ? new Date(data.generated_at).toLocaleString() : "?"],
    ["duration", fmtDuration(data.duration)],
  ].filter(Boolean);

  return el(
    "header",
    { class: "masthead" },
    el(
      "div",
      { class: "masthead-top" },
      el(
        "div",
        {},
        el(
          "h1",
          {},
          "googletrans-curl ",
          el("span", { class: "dim", text: "test dashboard" }),
        ),
        el(
          "p",
          { class: "sub" },
          "Release-gate results for the package under test — ",
          el("a", {
            href: "https://github.com/kreier/googletrans-curl",
            text: "kreier/googletrans-curl",
          }),
          " (fork of ",
          el("a", { href: "https://github.com/ssut/py-googletrans", text: "py-googletrans" }),
          ").",
        ),
      ),
      el("span", {
        class: `exit-pill ${exit === 0 ? "exit-ok" : "exit-bad"}`,
        text: exit === 0 ? "exit status 0" : `exit status ${exit}`,
      }),
    ),
    el(
      "ul",
      { class: "meta" },
      ...meta.map(([key, value]) =>
        el("li", {}, el("span", { class: "k", text: key }), el("b", { text: value })),
      ),
    ),
  );
}

function banner(exit) {
  return el(
    "div",
    { class: "banner" },
    el("strong", { text: `pytest exited with status ${exit}. ` }),
    "Failed tests are listed below with their output. An ",
    el("span", { class: "badge badge-xpassed", text: "xpassed" }),
    " entry means a known defect was fixed — remove its xfail marker as part of the release gate.",
  );
}

function explainer(summary) {
  if (!summary.xfailed && !summary.xpassed) return null;
  return el(
    "p",
    { class: "explainer" },
    el("span", { class: "badge badge-xfailed", text: "xfailed" }),
    " marks a known pre-release defect: failing is the expected outcome today. These markers are strict — if one of them starts passing, the run goes red and the marker must be removed. See AGENTS.md in the repository.",
  );
}

function bar(counts) {
  return el(
    "div",
    { class: "bar" },
    ...OUTCOME_ORDER.filter((outcome) => counts[outcome]).map((outcome) =>
      el("span", {
        class: `seg seg-${outcome}`,
        style: `flex-grow: ${counts[outcome]}`,
        title: `${counts[outcome]} ${OUTCOME_LABELS[outcome]}`,
      }),
    ),
  );
}

function testBody(test) {
  const rows = [kv("nodeid", el("code", { text: test.nodeid }))];
  if (test.markers?.length) {
    rows.push(
      kv(
        "markers",
        el(
          "span",
          { class: "pill-list" },
          ...test.markers.map((marker) => el("code", { class: "marker", text: marker })),
        ),
      ),
    );
  }
  if (test.strict) {
    rows.push(kv("strict", el("span", { text: "xpassed under strict xfail — this fails the run" })));
  }
  if (test.reason) rows.push(kv("reason", el("span", { class: "reason-text", text: test.reason })));

  return el(
    "div",
    { class: "test-body" },
    ...rows,
    test.source ? block("source", test.source) : null,
    test.stdout ? block("stdout", test.stdout) : null,
    test.detail ? block("output", test.detail) : null,
  );
}

function testRow(test) {
  return el(
    "details",
    { class: `test test-${test.outcome}` },
    el(
      "summary",
      {},
      el("span", { class: "chevron" }),
      badge(test.outcome),
      el("span", { class: "test-name", text: test.name }),
      el("span", { class: "spacer" }),
      el("span", { class: "duration", text: fmtDuration(test.duration) }),
    ),
    testBody(test),
  );
}

function moduleSection(module) {
  const counts = {};
  for (const test of module.tests) counts[test.outcome] = (counts[test.outcome] ?? 0) + 1;
  const sub = OUTCOME_ORDER.filter((outcome) => counts[outcome])
    .map((outcome) => `${counts[outcome]} ${OUTCOME_LABELS[outcome]}`)
    .join(" · ");

  return el(
    "section",
    { class: "module" },
    el(
      "div",
      { class: "module-head" },
      el(
        "div",
        { class: "module-title" },
        el("h2", { text: module.name }),
        el("span", { class: "module-sub", text: `${module.tests.length} tests · ${sub}` }),
      ),
      bar(counts),
    ),
    el("div", { class: "tests" }, ...module.tests.map(testRow)),
  );
}

function footer() {
  return el(
    "footer",
    { class: "footer" },
    "generated by ",
    el("code", { text: "python -m pytest --report-file dashboard/public/results.json" }),
    " · source: ",
    el("a", {
      href: "https://github.com/flynn0/googletrans-curl-tester",
      text: "flynn0/googletrans-curl-tester",
    }),
  );
}

function render(app, data) {
  const summary = data.summary ?? {};
  const failed = (summary.failed ?? 0) + (summary.errors ?? 0);
  const exit = data.exit_status ?? 0;

  app.append(
    el(
      "div",
      { class: "shell" },
      masthead(data, exit),
      exit !== 0 ? banner(exit) : null,
      el(
        "section",
        { class: "cards" },
        card(summary.total ?? 0, "tests"),
        card(summary.passed ?? 0, "passed", "tone-ok"),
        card(failed, "failed", failed ? "tone-bad" : ""),
        card(summary.skipped ?? 0, "skipped"),
        card(summary.xfailed ?? 0, "xfailed", summary.xfailed ? "tone-warn" : ""),
        card(summary.xpassed ?? 0, "xpassed", summary.xpassed ? "tone-bad" : ""),
      ),
      explainer(summary),
      ...(data.modules ?? []).map(moduleSection),
      footer(),
    ),
  );
}

function renderError(app, error) {
  app.append(
    el(
      "div",
      { class: "shell" },
      el(
        "header",
        { class: "masthead" },
        el(
          "h1",
          {},
          "googletrans-curl ",
          el("span", { class: "dim", text: "test dashboard" }),
        ),
      ),
      el(
        "div",
        { class: "banner" },
        el("strong", { text: "results.json could not be loaded. " }),
        `(${error.message}) Generate it with:`,
      ),
      el("pre", {
        class: "block standalone",
        text: "python -m pytest --report-file dashboard/public/results.json\ncd dashboard && npm run build",
      }),
    ),
  );
}

async function init() {
  const app = document.getElementById("app");
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status} for ${DATA_URL}`);
    render(app, await response.json());
  } catch (error) {
    renderError(app, error);
  }
}

init();
