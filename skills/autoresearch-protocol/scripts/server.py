#!/usr/bin/env python3
"""
Autoresearch dashboard — serves http://localhost:8765
Renders the human report (report.md) AND the numeric trend (results.md) on one page.
Reads both files on every request; auto-refreshes with ?watch=1
Usage: python server.py [--port 8765]

Written into a loop folder only when the loop config has output_dashboard: on.
Stdlib only + Chart.js from CDN — no pip installs required.
"""
import argparse
import html as html_lib
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(__file__)
RESULTS_FILE = os.path.join(HERE, "results.md")
THETASK_FILE = os.path.join(HERE, "__thetask__.md")
REPORT_FILE = os.path.join(HERE, "report.md")


def parse_results():
    """Parse results.md table into list of dicts."""
    rows = []
    if not os.path.exists(RESULTS_FILE):
        return rows
    with open(RESULTS_FILE, encoding="utf-8") as f:
        content = f.read()
    in_table = False
    headers = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("| #") or line.startswith("|#"):
            headers = [h.strip() for h in line.strip("|").split("|")]
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= len(headers):
                rows.append(dict(zip(headers, cells)))
        elif in_table and not line.startswith("|"):
            if line.startswith("---"):
                continue  # section divider in results
    return rows


def parse_thetask():
    """Return task description and tracked files from __thetask__.md."""
    if not os.path.exists(THETASK_FILE):
        return "", [], "history/v000", 0
    with open(THETASK_FILE, encoding="utf-8") as f:
        content = f.read()
    desc = re.search(r"## Task description\n(.+?)(?:\n##|\Z)", content, re.S)
    desc = desc.group(1).strip() if desc else ""
    files_section = re.search(r"## Tracked files\n(.+?)(?:\n##|\Z)", content, re.S)
    files = []
    if files_section:
        for line in files_section.group(1).splitlines():
            line = line.strip().strip("-").strip().strip("`")
            if line:
                files.append(line)
    best = re.search(r"## Current best snapshot\n(.+)", content)
    best = best.group(1).strip() if best else "history/v000"
    iters = re.search(r"## Iterations run\n(\d+)", content)
    iters = int(iters.group(1)) if iters else 0
    return desc, files, best, iters


def parse_report():
    """Split report.md into (open_questions list, rest-of-report markdown)."""
    if not os.path.exists(REPORT_FILE):
        return [], ""
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    questions = []
    q_match = re.search(r"## Open questions[^\n]*\n(.+?)(?:\n## |\Z)", content, re.S)
    if q_match:
        for line in q_match.group(1).splitlines():
            line = line.strip()
            if line.startswith("-"):
                questions.append(line.lstrip("-").strip())
    # rest = everything except the open-questions section
    rest = re.sub(r"## Open questions[^\n]*\n.+?(?=\n## |\Z)", "", content, flags=re.S)
    return questions, rest.strip()


def md_to_html(text):
    """Minimal markdown → HTML for the report body (headings, bold, lists, paragraphs)."""
    out = []
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h2>{_inline(line[2:])}</h2>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h3>{_inline(line[3:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif not line:
            if in_list:
                out.append("</ul>"); in_list = False
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _inline(s):
    s = html_lib.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def build_html(rows, desc, files, best, iters, questions, report_rest, watch):
    labels = [r.get("#", "") for r in rows]
    running = []
    for r in rows:
        try:
            running.append(float(r.get("Running", 0)))
        except ValueError:
            running.append(0)

    # collect numeric columns (anything after "Next focus")
    all_keys = list(rows[0].keys()) if rows else []
    std_keys = {"#", "Verdict", "Δ", "Running", "Decision", "Next focus"}
    num_keys = [k for k in all_keys if k not in std_keys and k]

    num_datasets = []
    for key in num_keys:
        vals = []
        for r in rows:
            try:
                vals.append(float(r.get(key, "").replace("—", "").replace("nan", "") or "nan"))
            except ValueError:
                vals.append(None)
        num_datasets.append({"label": key, "data": vals})

    last_focus = rows[-1].get("Next focus", "—") if rows else "—"
    plateau = any("PLATEAU" in r.get("Decision", "") for r in rows)
    refresh = '<meta http-equiv="refresh" content="30">' if watch else ""

    questions_html = ""
    if questions:
        items = "".join(f"<li>{_inline(q)}</li>" for q in questions)
        questions_html = f"""
        <div class="questions">
          <div class="q-title">⚑ Open questions for you</div>
          <ul>{items}</ul>
          <div class="q-hint">Answer in your session (e.g. <code>A3: ...</code>) or in answers.md</div>
        </div>"""

    report_html = f'<div class="report">{md_to_html(report_rest)}</div>' if report_rest else ""

    num_charts_html = ""
    for ds in num_datasets:
        clean_vals = [v if v is not None else "null" for v in ds["data"]]
        num_charts_html += f"""
        <div class="chart-wrap">
          <canvas id="chart_{ds['label']}"></canvas>
        </div>
        <script>
        new Chart(document.getElementById('chart_{ds["label"]}'), {{
          type: 'line',
          data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
              label: '{ds["label"]}',
              data: {json.dumps(clean_vals)},
              borderColor: '#a78bfa',
              backgroundColor: 'rgba(167,139,250,0.15)',
              tension: 0.3,
              spanGaps: true,
            }}]
          }},
          options: {{ responsive: true, plugins: {{ legend: {{ display: true }} }} }}
        }});
        </script>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{refresh}
<title>Autoresearch Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f0f13; color: #e2e8f0; margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; color: #c4b5fd; }}
  h2 {{ font-size: 1.1rem; color: #c4b5fd; margin: 18px 0 6px; }}
  h3 {{ font-size: 0.95rem; color: #a5b4fc; margin: 14px 0 4px; }}
  .meta {{ font-size: 0.82rem; color: #94a3b8; margin-bottom: 20px; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .card {{ background: #1e1e2e; border-radius: 10px; padding: 16px 20px; min-width: 160px; }}
  .card-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }}
  .card-value {{ font-size: 1.6rem; font-weight: 700; color: #c4b5fd; }}
  .plateau {{ color: #f59e0b; font-weight: bold; }}
  .chart-wrap {{ background: #1e1e2e; border-radius: 10px; padding: 16px; margin-bottom: 20px; }}
  .focus-box {{ background: #1e1e2e; border-left: 3px solid #c4b5fd; padding: 12px 16px;
                border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 0.9rem; }}
  .files {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
  .questions {{ background: #2a2410; border: 1px solid #f59e0b; border-radius: 10px;
                padding: 14px 18px; margin-bottom: 22px; }}
  .q-title {{ color: #fbbf24; font-weight: 700; margin-bottom: 6px; }}
  .q-hint {{ font-size: 0.78rem; color: #94a3b8; margin-top: 6px; }}
  .report {{ background: #1e1e2e; border-radius: 10px; padding: 4px 20px 16px; margin-bottom: 24px; font-size: 0.9rem; }}
  code {{ background: #2d2d3d; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }}
  ul {{ margin: 4px 0; }}
</style>
</head>
<body>
<h1>Autoresearch Dashboard</h1>
<div class="meta">{html_lib.escape(desc)}</div>
<div class="files">Tracked: {" &nbsp;·&nbsp; ".join(html_lib.escape(f) for f in files)}</div>
<div class="meta">Best snapshot: {best} &nbsp;·&nbsp; Iterations: {iters}</div>

{questions_html}

<div class="cards">
  <div class="card"><div class="card-label">Iterations</div><div class="card-value">{iters}</div></div>
  <div class="card"><div class="card-label">Running quality</div>
    <div class="card-value">{running[-1] if running else 0:+.0f}</div></div>
  <div class="card"><div class="card-label">Last verdict</div>
    <div class="card-value" style="font-size:1.1rem">{rows[-1].get("Verdict","—") if rows else "—"}</div></div>
  {"<div class='card'><div class='card-label plateau'>⚠ Plateau</div><div class='card-value plateau'>5 REVERTs</div></div>" if plateau else ""}
</div>

{report_html}

<div class="focus-box"><strong>Next focus:</strong> {html_lib.escape(last_focus)}</div>

<div class="chart-wrap">
  <canvas id="qualityChart"></canvas>
</div>
<script>
new Chart(document.getElementById('qualityChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [
      {{
        label: 'Running quality',
        data: {json.dumps(running)},
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129,140,248,0.1)',
        tension: 0.2,
        fill: true,
      }},
      {{
        label: 'KEPT',
        data: {json.dumps([r.get("Running") if "KEPT" in r.get("Decision","") else None for r in rows])},
        borderColor: 'rgba(0,0,0,0)',
        backgroundColor: '#34d399',
        pointRadius: 7,
        pointHoverRadius: 9,
        showLine: false,
        spanGaps: false,
      }},
      {{
        label: 'REVERTED',
        data: {json.dumps([r.get("Running") if "REVERTED" in r.get("Decision","") else None for r in rows])},
        borderColor: 'rgba(0,0,0,0)',
        backgroundColor: '#f87171',
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: false,
        spanGaps: false,
      }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: true }} }},
    scales: {{ y: {{ grid: {{ color: '#2d2d3d' }}, ticks: {{ color: '#94a3b8' }} }},
               x: {{ grid: {{ color: '#2d2d3d' }}, ticks: {{ color: '#94a3b8' }} }} }}
  }}
}});
</script>

{num_charts_html}

</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs

    def do_GET(self):
        watch = "watch=1" in self.path
        rows = parse_results()
        desc, files, best, iters = parse_thetask()
        questions, report_rest = parse_report()
        html = build_html(rows, desc, files, best, iters, questions, report_rest, watch)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Autoresearch dashboard → http://localhost:{args.port}")
    print(f"Auto-refresh: http://localhost:{args.port}?watch=1")
    print("Ctrl-C to stop")
    HTTPServer(("", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
