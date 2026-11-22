#!/usr/bin/env python3
"""Generate a Matrix-style system status SVG for the GitHub profile.

The panel is intentionally qualitative: it shows the 24-month contribution
window, current focus and missions, without relying on a dense activity feed.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

GRAPHQL = "https://api.github.com/graphql"
QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

MONO = "ui-monospace,'SF Mono',Menlo,Consolas,'Courier New',monospace"

THEMES = {
    "dark": {
        "bg": "#050805",
        "border": "#0A3A1B",
        "primary": "#00FF41",
        "secondary": "#9DFFB0",
        "text": "#C9D1D9",
        "muted": "#4E9A5B",
        "bars": ["#0A1A10", "#0A3A1B", "#006622", "#00A838", "#22D744"],
    },
    "light": {
        "bg": "#F6FFF8",
        "border": "#B7E4C7",
        "primary": "#007A1F",
        "secondary": "#2D6A4F",
        "text": "#1F3D2B",
        "muted": "#4E9A5B",
        "bars": ["#E6F4EA", "#B7E4C7", "#74C69D", "#2D6A4F", "#081C15"],
    },
}


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    try:
        return subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def fetch_window(user, start, end, tok):
    payload = {
        "query": QUERY,
        "variables": {
            "login": user,
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    request = urllib.request.Request(
        GRAPHQL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
            "User-Agent": user,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        sys.exit(f"GitHub API error: {data['errors']}")
    node = data.get("data", {}).get("user")
    if not node:
        sys.exit(f"GitHub user not found: {user}")
    weeks = node["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [day for week in weeks for day in week["contributionDays"]]


def month_keys(end, count=24):
    keys = []
    year, month = end.year, end.month
    for _ in range(count):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


def bar_level(value, maximum):
    if value <= 0:
        return 0
    ratio = value / maximum
    if ratio <= 0.25:
        return 1
    if ratio <= 0.50:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def render(theme_name, contributions, active_months, buckets, maximum):
    t = THEMES[theme_name]
    width, height = 800, 340
    keys = list(buckets)
    total = sum(buckets.values())

    bars = []
    year_labels = []
    for index, key in enumerate(keys):
        value = buckets[key]
        bar_height = 4 + round(38 * value / maximum)
        x = 410 + index * 15
        y = 158 - bar_height
        bars.append(
            f'<rect x="{x}" y="{y}" width="12" height="{bar_height}" rx="2" '
            f'fill="{t["bars"][bar_level(value, maximum)]}"/>'
        )
        if key.endswith("-01"):
            year_labels.append(
                f'<text class="meta" x="{x + 6}" y="176" text-anchor="middle">{key[:4]}</text>'
            )

    desc = (
        f"{total} contributions across {active_months} active months. "
        "Core: Kubernetes, event-driven architecture, OpenTelemetry, LLM. "
        "Current mission: access-control platform. Private work not public."
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
  <title id="t">System status — Software Architect, 24 months</title>
  <desc id="d">{escape(desc)}</desc>
  <style>
    text {{ font-family: {MONO}; }}
    .head {{ font-size: 12px; font-weight: 700; fill: {t["primary"]}; letter-spacing: 1.5px; }}
    .meta {{ font-size: 9.5px; fill: {t["muted"]}; letter-spacing: .8px; }}
    .label {{ font-size: 9.5px; fill: {t["muted"]}; letter-spacing: 1.2px; }}
    .value {{ font-size: 12px; font-weight: 600; fill: {t["text"]}; }}
    .accent {{ fill: {t["primary"]}; }}
    .secondary {{ fill: {t["secondary"]}; }}
    .mission {{ font-size: 10.5px; fill: {t["text"]}; }}
    .mission-title {{ font-size: 10.5px; fill: {t["primary"]}; }}
    .cursor {{ animation: blink 1.2s steps(1) infinite; }}
    .pulse {{ animation: pulse 2.6s ease-in-out infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .3; }} }}
    @media (prefers-reduced-motion: reduce) {{ .cursor, .pulse {{ animation: none; }} }}
  </style>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>
  <circle class="pulse" cx="30" cy="28" r="3.5" fill="{t["primary"]}"/>
  <text class="head" x="42" y="32">SYSTEM STATUS // ONLINE</text>
  <text class="meta" x="772" y="32" text-anchor="end">SYNC 12H</text>
  <line x1="28" y1="44" x2="772" y2="44" stroke="{t["border"]}"/>

  <text class="label" x="28" y="68">ROLE</text>
  <text class="value" x="142" y="68">Software Architect</text>
  <text class="label" x="28" y="94">WINDOW</text>
  <text class="value" x="142" y="94">24 months</text>
  <text class="label" x="28" y="120">CONTRIBUTIONS</text>
  <text class="value" x="142" y="120">{total:,}</text>
  <text class="label" x="28" y="146">ACTIVE MONTHS</text>
  <text class="value" x="142" y="146">{active_months}/24</text>
  <text class="label" x="28" y="172">PRIVATE WORK</text>
  <text class="value secondary" x="142" y="172">NOT PUBLIC</text>
  <text class="label" x="28" y="198">CURRENT</text>
  <text class="value accent" x="142" y="198">access-control platform</text>

  <text class="meta" x="410" y="88">24M SIGNAL</text>
  {chr(10).join("  " + bar for bar in bars)}
  {chr(10).join("  " + label for label in year_labels)}

  <text class="meta" x="410" y="198">CORE</text>
  <text class="value" x="410" y="216">K8s · Event-Driven</text>
  <text class="value" x="410" y="232">OTEL · LLM</text>

  <line x1="28" y1="250" x2="772" y2="250" stroke="{t["border"]}"/>
  <text class="mission-title" x="28" y="270">&gt; mission_log<tspan class="cursor">_</tspan></text>
  <text class="mission" x="28" y="290"><tspan class="accent">-</tspan> access-control platform · in progress</text>
  <text class="mission" x="28" y="308"><tspan class="accent">-</tspan> draiver-flow · private</text>
  <text class="mission" x="28" y="326"><tspan class="accent">-</tspan> agentic workflows / local inference · ongoing</text>
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description="Generate a Matrix-style GitHub system status SVG.")
    parser.add_argument("--user", default=os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER"))
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--prefix", default="github-status-matrix")
    args = parser.parse_args()
    if not args.user:
        sys.exit("error: --user is required (or set GH_USER / GITHUB_REPOSITORY_OWNER)")

    tok = token()
    if not tok:
        sys.exit("error: no token found. set GH_TOKEN (or GITHUB_TOKEN).")

    end = datetime.now(timezone.utc).replace(microsecond=0)
    mid = end - timedelta(days=365)
    start = mid - timedelta(days=365)

    # contributionsCollection accepts at most one year per query, so fetch two
    # 365-day windows and de-duplicate days at the boundary.
    days = {}
    for window_start, window_end in ((start, mid), (mid, end)):
        for day in fetch_window(args.user, window_start, window_end, tok):
            days[day["date"]] = day["contributionCount"]

    today = end.date()
    keys = month_keys(today)
    buckets = {key: 0 for key in keys}
    for date, count in days.items():
        day = datetime.strptime(date, "%Y-%m-%d").date()
        if day > today:
            continue
        key = date[:7]
        if key in buckets:
            buckets[key] += count

    total = sum(buckets.values())
    active_months = sum(1 for value in buckets.values() if value > 0)
    maximum = max(buckets.values(), default=0) or 1

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        path = output / f"{args.prefix}-{theme}.svg"
        path.write_text(render(theme, total, active_months, buckets, maximum))
        print(f"wrote {path} — {total} contributions, {active_months}/24 active months")


if __name__ == "__main__":
    main()
