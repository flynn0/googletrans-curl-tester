import "./style.css";

const DATA_URL = `${import.meta.env.BASE_URL}results.json`;
const HISTORY_URL = `${import.meta.env.BASE_URL}history.json`;
const RELEASE_VERSION = "0.2.0";

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

function parseUtcDate(str) {
  const [y, m, d] = str.slice(0, 10).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function fmtDate(dateStr) {
  if (!dateStr) return "";
  const d = parseUtcDate(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}

function fmtDateTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
    timeZone: "UTC",
  });
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

function getTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) return saved;
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

function updateToggleBtn(btn, theme) {
  const icon = btn.querySelector(".theme-icon");
  const text = btn.querySelector(".theme-text");
  if (icon) icon.textContent = theme === "dark" ? "🌙" : "☀️";
  if (text) text.textContent = theme === "dark" ? "Dark" : "Light";
}

function themeToggle() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || getTheme();
  const btn = el(
    "button",
    {
      id: "theme-toggle",
      class: "theme-toggle",
      type: "button",
      "aria-label": "Toggle color theme",
      onclick: () => {
        const active = document.documentElement.getAttribute("data-theme") || getTheme();
        const next = active === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
        updateToggleBtn(btn, next);
      },
    },
    el("span", { class: "theme-icon", text: currentTheme === "dark" ? "🌙" : "☀️" }),
    el("span", { class: "theme-text", text: currentTheme === "dark" ? "Dark" : "Light" }),
  );
  return btn;
}

function initThemeListener() {
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
      if (!localStorage.getItem("theme")) {
        const theme = e.matches ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", theme);
        const btn = document.getElementById("theme-toggle");
        if (btn) updateToggleBtn(btn, theme);
      }
    });
  }
}

function masthead(data, exit) {
  const env = data.environment ?? {};
  const git = env.git;
  const targets =
    (env.targets ?? []).map((t) => `${t.distribution} ${t.version}`).join(", ") ||
    "not installed";

  const meta = [
    ["release", `v${RELEASE_VERSION}`],
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
          el("a", {
            class: "version-badge",
            href: `https://github.com/flynn0/googletrans-curl-tester/releases/tag/v${RELEASE_VERSION}`,
            title: `Release v${RELEASE_VERSION}`,
            text: `v${RELEASE_VERSION}`,
          }),
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
      el(
        "div",
        { class: "masthead-actions" },
        themeToggle(),
        el("span", {
          class: `exit-pill ${exit === 0 ? "exit-ok" : "exit-bad"}`,
          text: exit === 0 ? "exit status 0" : `exit status ${exit}`,
        }),
      ),
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

// ---------------------------------------------------------------------------
// 30 Tickbar Indicator Component
// ---------------------------------------------------------------------------

function tickbarSection(history) {
  if (!history || !history.runs || history.runs.length === 0) return null;

  const runs = history.runs;
  let mode = "runs"; // "runs" or "days"

  const container = el("section", { class: "history-section" });
  const detailPanel = el("div", { class: "tick-detail-panel" });
  const trackWrap = el("div", { class: "tick-track-wrap" });

  function showRunDetail(run) {
    detailPanel.replaceChildren();
    if (!run) {
      detailPanel.append(el("span", { text: "Hover over or tap a tick to view run details." }));
      return;
    }
    const isSuccess = run.conclusion === "success";
    const statusBadge = el("span", {
      class: `badge ${isSuccess ? "badge-passed" : "badge-failed"}`,
      text: isSuccess ? "Passed" : (run.conclusion ?? "Failed"),
    });

    const metaLeft = el(
      "div",
      { class: "run-meta-left" },
      statusBadge,
      el("strong", { text: run.name || run.workflow || "Run" }),
      el("span", { class: "dim", text: `(${run.event})` }),
      run.commit
        ? el("a", {
            href: `https://github.com/flynn0/googletrans-curl-tester/commit/${run.commit}`,
            text: run.commit,
            target: "_blank",
            rel: "noreferrer",
          })
        : null,
    );

    const metaRight = el(
      "div",
      { class: "run-meta-right" },
      el("span", { text: fmtDateTime(run.created_at) }),
      run.duration ? el("span", { class: "duration", text: fmtDuration(run.duration) }) : null,
      run.url
        ? el("a", {
            href: run.url,
            text: "View Run ↗",
            target: "_blank",
            rel: "noreferrer",
          })
        : null,
    );

    detailPanel.append(metaLeft, metaRight);
  }

  function showDayDetail(dayInfo) {
    detailPanel.replaceChildren();
    if (!dayInfo) {
      detailPanel.append(el("span", { text: "Hover over or tap a tick to view day details." }));
      return;
    }

    const { dateStr, total, success, failure } = dayInfo;
    let badgeNode;
    if (total === 0) {
      badgeNode = el("span", { class: "badge badge-skipped", text: "No runs" });
    } else if (failure === 0) {
      badgeNode = el("span", { class: "badge badge-passed", text: "100% Passed" });
    } else if (success === 0) {
      badgeNode = el("span", { class: "badge badge-failed", text: "Failed" });
    } else {
      badgeNode = el("span", { class: "badge badge-xfailed", text: `${success}/${total} Passed` });
    }

    const metaLeft = el(
      "div",
      { class: "run-meta-left" },
      badgeNode,
      el("strong", { text: fmtDate(dateStr) }),
      el("span", { text: `${total} run${total === 1 ? "" : "s"} (${success} passed, ${failure} failed)` }),
    );

    const metaRight = el(
      "div",
      { class: "run-meta-right" },
      total > 0 ? el("span", { text: `${Math.round((success / total) * 100)}% daily success rate` }) : null,
    );

    detailPanel.append(metaLeft, metaRight);
  }

  function renderTicks() {
    trackWrap.replaceChildren();
    const tickBar = el("div", { class: "tick-bar" });

    if (mode === "runs") {
      const slice = runs.slice(-30);
      const totalInSlice = slice.length;
      const successInSlice = slice.filter((r) => r.conclusion === "success").length;
      const rate = totalInSlice > 0 ? ((successInSlice / totalInSlice) * 100).toFixed(1) : 0;
      reliabilityPill.textContent = `${rate}% passed (${successInSlice}/${totalInSlice} runs)`;

      // If fewer than 30, pad front
      const padCount = Math.max(0, 30 - slice.length);
      for (let i = 0; i < padCount; i++) {
        tickBar.append(el("div", { class: "tick-item tick-empty", title: "No run" }));
      }

      slice.forEach((run, idx) => {
        const isSuccess = run.conclusion === "success";
        const tick = el("div", {
          class: `tick-item ${isSuccess ? "tick-success" : "tick-failure"}`,
          tabindex: "0",
          title: `${run.name || run.workflow} · ${run.conclusion} · ${fmtDateTime(run.created_at)}`,
          onmouseenter: () => showRunDetail(run),
          onfocus: () => showRunDetail(run),
        });
        tickBar.append(tick);
      });

      trackWrap.append(
        tickBar,
        el(
          "div",
          { class: "tick-labels" },
          el("span", { text: `${totalInSlice} runs ago` }),
          el("span", { text: "Latest run (today)" }),
        ),
      );

      // Default detail is the latest run
      showRunDetail(slice[slice.length - 1]);
    } else {
      // 30 days mode
      const now = new Date();
      const days = [];
      for (let i = 29; i >= 0; i--) {
        const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i));
        const dateStr = d.toISOString().slice(0, 10);
        const dayRuns = runs.filter((r) => (r.created_at || "").slice(0, 10) === dateStr);
        const success = dayRuns.filter((r) => r.conclusion === "success").length;
        const failure = dayRuns.filter((r) => r.conclusion !== "success").length;
        days.push({
          dateStr,
          total: dayRuns.length,
          success,
          failure,
          runs: dayRuns,
        });
      }

      const activeDays = days.filter((d) => d.total > 0);
      const totalRunsIn30Days = activeDays.reduce((acc, d) => acc + d.total, 0);
      const successfulRunsIn30Days = activeDays.reduce((acc, d) => acc + d.success, 0);
      const rate =
        totalRunsIn30Days > 0 ? ((successfulRunsIn30Days / totalRunsIn30Days) * 100).toFixed(1) : 0;
      reliabilityPill.textContent = `${rate}% passed (${activeDays.length}/30 days active)`;

      days.forEach((dayInfo) => {
        let cls = "tick-empty";
        if (dayInfo.total > 0) {
          if (dayInfo.failure === 0) cls = "tick-success";
          else if (dayInfo.success === 0) cls = "tick-failure";
          else cls = "tick-mixed";
        }
        const tick = el("div", {
          class: `tick-item ${cls}`,
          tabindex: "0",
          title: `${fmtDate(dayInfo.dateStr)}: ${dayInfo.total} runs (${dayInfo.success} passed, ${dayInfo.failure} failed)`,
          onmouseenter: () => showDayDetail(dayInfo),
          onfocus: () => showDayDetail(dayInfo),
        });
        tickBar.append(tick);
      });

      trackWrap.append(
        tickBar,
        el(
          "div",
          { class: "tick-labels" },
          el("span", { text: `30 days ago (${fmtDate(days[0].dateStr)})` }),
          el("span", { text: `Today (${fmtDate(days[days.length - 1].dateStr)})` }),
        ),
      );

      // Default detail is today
      showDayDetail(days[days.length - 1]);
    }
  }

  const reliabilityPill = el("span", { class: "reliability-badge", text: "..." });

  const btnRuns = el("button", {
    class: "view-toggle-btn active",
    type: "button",
    text: "Last 30 runs",
    onclick: () => {
      if (mode === "runs") return;
      mode = "runs";
      btnRuns.classList.add("active");
      btnDays.classList.remove("active");
      renderTicks();
    },
  });

  const btnDays = el("button", {
    class: "view-toggle-btn",
    type: "button",
    text: "Last 30 days",
    onclick: () => {
      if (mode === "days") return;
      mode = "days";
      btnDays.classList.add("active");
      btnRuns.classList.remove("active");
      renderTicks();
    },
  });

  const header = el(
    "div",
    { class: "history-header" },
    el(
      "div",
      { class: "history-title-group" },
      el("h2", {}, "Test Reliability Indicator", reliabilityPill),
      el("p", { class: "history-sub", text: "Continuous tracking of test executions and health" }),
    ),
    el("div", { class: "view-toggle" }, btnRuns, btnDays),
  );

  container.append(header, trackWrap, detailPanel);
  renderTicks();
  return container;
}

// ---------------------------------------------------------------------------
// Heatmap of Successful Runs Component
// ---------------------------------------------------------------------------

function heatmapSection(history) {
  if (!history || !history.runs || history.runs.length === 0) return null;

  const runs = history.runs;
  const byDate = {};
  for (const r of runs) {
    const d = (r.created_at || "").slice(0, 10);
    if (!d) continue;
    if (!byDate[d]) byDate[d] = { total: 0, success: 0, failure: 0, runs: [] };
    byDate[d].total += 1;
    if (r.conclusion === "success") byDate[d].success += 1;
    else byDate[d].failure += 1;
    byDate[d].runs.push(r);
  }

  // Earliest date (at least Oct 7, 2026) and latest date (at least today)
  const dateKeys = Object.keys(byDate).sort();
  const firstDateStr = dateKeys[0] || "2026-10-07";
  const lastDateStr = dateKeys[dateKeys.length - 1] || new Date().toISOString().slice(0, 10);

  const firstDate = parseUtcDate(firstDateStr);
  const lastDate = parseUtcDate(lastDateStr);

  // Align start to the preceding Sunday
  const calendarStart = new Date(firstDate);
  calendarStart.setUTCDate(calendarStart.getUTCDate() - calendarStart.getUTCDay());

  // Align end to the following Saturday
  const calendarEnd = new Date(lastDate);
  calendarEnd.setUTCDate(calendarEnd.getUTCDate() + (6 - calendarEnd.getUTCDay()));

  // Generate week columns (each column = 7 days Sun-Sat)
  const weeks = [];
  let curr = new Date(calendarStart);
  while (curr <= calendarEnd) {
    const week = [];
    for (let day = 0; day < 7; day++) {
      const dStr = curr.toISOString().slice(0, 10);
      week.push({
        date: new Date(curr),
        dateStr: dStr,
        dayOfWeek: day,
        data: byDate[dStr] || { total: 0, success: 0, failure: 0, runs: [] },
      });
      curr.setUTCDate(curr.getUTCDate() + 1);
    }
    weeks.push(week);
  }

  const container = el("section", { class: "history-section" });
  const dayDetailsWrap = el("div", { class: "day-details-panel", style: "display: none;" });

  function openDayRuns(dayObj) {
    dayDetailsWrap.replaceChildren();
    if (!dayObj || dayObj.data.total === 0) {
      dayDetailsWrap.style.display = "none";
      return;
    }

    const { dateStr, data } = dayObj;
    const header = el(
      "div",
      { class: "day-details-header" },
      el(
        "span",
        { class: "day-details-title" },
        `Runs on ${fmtDate(dateStr)} `,
        el("span", {
          class: "dim",
          text: `(${data.total} run${data.total === 1 ? "" : "s"}: ${data.success} passed, ${data.failure} failed)`,
        }),
      ),
      el("button", {
        class: "theme-toggle",
        type: "button",
        text: "Close ✕",
        onclick: () => {
          dayDetailsWrap.style.display = "none";
          container.querySelectorAll(".heatmap-cell.active").forEach((c) => c.classList.remove("active"));
        },
      }),
    );

    const runItems = data.runs.map((r) => {
      const isSuccess = r.conclusion === "success";
      return el(
        "div",
        { class: "day-run-item" },
        el(
          "div",
          { class: "run-meta-left" },
          el("span", {
            class: `badge ${isSuccess ? "badge-passed" : "badge-failed"}`,
            text: isSuccess ? "Passed" : (r.conclusion ?? "Failed"),
          }),
          el("strong", { text: r.name || r.workflow }),
          el("span", { class: "dim", text: `[${r.event}]` }),
          r.commit
            ? el("a", {
                href: `https://github.com/flynn0/googletrans-curl-tester/commit/${r.commit}`,
                text: r.commit,
                target: "_blank",
                rel: "noreferrer",
              })
            : null,
        ),
        el(
          "div",
          { class: "run-meta-right" },
          el("span", { text: fmtDateTime(r.created_at) }),
          r.duration ? el("span", { class: "duration", text: fmtDuration(r.duration) }) : null,
          r.url
            ? el("a", {
                href: r.url,
                text: "GitHub Run ↗",
                target: "_blank",
                rel: "noreferrer",
              })
            : null,
        ),
      );
    });

    dayDetailsWrap.append(header, el("div", { class: "day-runs-list" }, ...runItems));
    dayDetailsWrap.style.display = "block";
  }

  // Month labels across top
  const monthsRow = el("div", { class: "heatmap-months-row" });
  let lastMonth = -1;
  const colWidth = 17; // 14px cell + 3px gap

  weeks.forEach((week, wIdx) => {
    // Check first day of week or middle day
    const m = week[0].date.getUTCMonth();
    if (m !== lastMonth) {
      lastMonth = m;
      const monthLabel = week[0].date.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
      const labelEl = el("span", {
        class: "heatmap-month-label",
        style: `left: ${28 + wIdx * colWidth}px`,
        text: monthLabel,
      });
      monthsRow.append(labelEl);
    }
  });

  // Weekdays labels column
  const weekdaysCol = el(
    "div",
    { class: "heatmap-weekdays" },
    el("span", { text: "" }),
    el("span", { text: "Mon" }),
    el("span", { text: "" }),
    el("span", { text: "Wed" }),
    el("span", { text: "" }),
    el("span", { text: "Fri" }),
    el("span", { text: "" }),
  );

  // Weeks grid
  const weeksRow = el("div", { class: "heatmap-weeks-row" });

  weeks.forEach((week) => {
    const col = el("div", { class: "heatmap-week-col" });
    week.forEach((dayObj) => {
      const { dateStr, data } = dayObj;
      let cellCls = "cell-empty";
      let cellTitle = `${fmtDate(dateStr)}: No runs recorded`;

      if (data.total > 0) {
        if (data.failure === 0) {
          if (data.success <= 2) cellCls = "cell-passed-1";
          else if (data.success <= 5) cellCls = "cell-passed-2";
          else cellCls = "cell-passed-3";
          cellTitle = `${fmtDate(dateStr)}: ${data.total} run${data.total === 1 ? "" : "s"} (all passed · 100%)`;
        } else if (data.success === 0) {
          cellCls = "cell-failed";
          cellTitle = `${fmtDate(dateStr)}: ${data.total} run${data.total === 1 ? "" : "s"} (all failed)`;
        } else {
          cellCls = "cell-mixed";
          cellTitle = `${fmtDate(dateStr)}: ${data.total} runs (${data.success} passed, ${data.failure} failed)`;
        }
      }

      const cell = el("div", {
        class: `heatmap-cell ${cellCls}`,
        tabindex: "0",
        title: cellTitle,
        onclick: () => {
          container.querySelectorAll(".heatmap-cell.active").forEach((c) => c.classList.remove("active"));
          if (data.total > 0) {
            cell.classList.add("active");
            openDayRuns(dayObj);
          } else {
            dayDetailsWrap.style.display = "none";
          }
        },
      });
      col.append(cell);
    });
    weeksRow.append(col);
  });

  const heatmapTable = el(
    "div",
    { class: "heatmap-table" },
    monthsRow,
    el("div", { class: "heatmap-body" }, weekdaysCol, weeksRow),
  );

  const summary = history.summary || {};
  const totalRuns = summary.total_runs ?? runs.length;
  const succRuns = summary.successful_runs ?? runs.filter((r) => r.conclusion === "success").length;
  const succRate = summary.success_rate ?? (totalRuns ? ((succRuns / totalRuns) * 100).toFixed(1) : 0);

  const header = el(
    "div",
    { class: "history-header" },
    el(
      "div",
      { class: "history-title-group" },
      el("h2", {}, "Run History & Success Heatmap"),
      el(
        "p",
        { class: "history-sub" },
        `Daily test runs since original launch on October 7, 2026 (${totalRuns} total runs, ${succRuns} passed · ${succRate}% overall success rate)`,
      ),
    ),
  );

  const legend = el(
    "div",
    { class: "heatmap-footer" },
    el("span", { text: "Click on any day cell to view individual workflow runs" }),
    el(
      "div",
      { class: "heatmap-legend" },
      el("span", { text: "Less" }),
      el("span", { class: "legend-cell cell-empty" }),
      el("span", { class: "legend-cell cell-passed-1" }),
      el("span", { class: "legend-cell cell-passed-2" }),
      el("span", { class: "legend-cell cell-passed-3" }),
      el("span", { text: "More" }),
      el(
        "span",
        { class: "legend-badge-item" },
        el("span", { class: "legend-cell cell-mixed" }),
        el("span", { text: "Mixed" }),
      ),
      el(
        "span",
        { class: "legend-badge-item" },
        el("span", { class: "legend-cell cell-failed" }),
        el("span", { text: "Failed" }),
      ),
    ),
  );

  container.append(header, el("div", { class: "heatmap-wrap" }, heatmapTable), legend, dayDetailsWrap);
  return container;
}

function footer() {
  return el(
    "footer",
    { class: "footer" },
    "googletrans-curl-tester ",
    el("b", { text: `v${RELEASE_VERSION}` }),
    " · generated by ",
    el("code", { text: "python -m pytest --report-file dashboard/public/results.json" }),
    " · source: ",
    el("a", {
      href: "https://github.com/flynn0/googletrans-curl-tester",
      text: "flynn0/googletrans-curl-tester",
    }),
  );
}

function render(app, data, historyData) {
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
      tickbarSection(historyData),
      heatmapSection(historyData),
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
          "div",
          { class: "masthead-top" },
          el(
            "h1",
            {},
            "googletrans-curl ",
            el("span", { class: "dim", text: "test dashboard" }),
            el("span", { class: "version-badge", text: `v${RELEASE_VERSION}` }),
          ),
          el(
            "div",
            { class: "masthead-actions" },
            themeToggle(),
          ),
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
  initThemeListener();
  const app = document.getElementById("app");
  try {
    const [resultsRes, historyRes] = await Promise.all([
      fetch(DATA_URL, { cache: "no-store" }),
      fetch(HISTORY_URL, { cache: "no-store" }).catch(() => null),
    ]);

    if (!resultsRes.ok) throw new Error(`HTTP ${resultsRes.status} for ${DATA_URL}`);
    const resultsData = await resultsRes.json();
    let historyData = null;
    if (historyRes && historyRes.ok) {
      try {
        historyData = await historyRes.json();
      } catch {
        historyData = null;
      }
    }

    render(app, resultsData, historyData);
  } catch (error) {
    renderError(app, error);
  }
}

init();
