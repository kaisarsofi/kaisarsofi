#!/usr/bin/env python3
"""Render Kaisar's contribution calendar from GitHub's public profile HTML."""

from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "kaisarsofi"
PALETTE = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")
CELL = 10
GAP = 4
STEP = CELL + GAP
LEFT = 52
TOP = 42
WEEKS = 53
DAYS = WEEKS * 7


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        if tag != "td":
            return
        cell = dict(attrs)
        day = cell.get("data-date")
        if not day:
            return
        try:
            count = int(cell.get("data-count", "0"))
            level = int(cell.get("data-level", "0"))
            self.days[date.fromisoformat(day)] = (count, max(0, min(level, 4)))
        except (TypeError, ValueError):
            return


def fetch_days():
    request = Request(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={
            "Accept": "text/html",
            "User-Agent": "kaisarsofi-profile-calendar/1.0",
        },
    )
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = ContributionParser()
    parser.feed(page)
    if not parser.days:
        raise RuntimeError("GitHub returned no public contribution-day cells")
    return parser.days


def render(days, today):
    current_week = today - timedelta(days=(today.weekday() + 1) % 7)
    start = current_week - timedelta(weeks=WEEKS - 1)
    cells = []
    total = 0
    month_labels = []

    for offset in range(DAYS):
        day = start + timedelta(days=offset)
        column, row = divmod(offset, 7)
        count, level = days.get(day, (0, 0))
        if day <= today:
            total += count
        if day.day <= 7 and (not month_labels or month_labels[-1][0] != column):
            month_labels.append((column, day.strftime("%b")))
        x = LEFT + column * STEP
        y = TOP + row * STEP
        delay = column * 0.035 + row * 0.012
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
            f'fill="{PALETTE[level]}"><title>{day.isoformat()}: {count} contributions</title>'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" '
            'dur="0.24s" fill="freeze"/></rect>'
        )

    months = "".join(
        f'<text x="{LEFT + column * STEP}" y="34" font-size="10" fill="#8b949e">'
        f"{escape(month)}</text>"
        for column, month in month_labels
    )
    count_label = f"{total:,} contributions in the last 53 weeks"
    if total == 1:
        count_label = "1 contribution in the last 53 weeks"

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="820" height="172" '
        'viewBox="0 0 820 172" role="img" aria-labelledby="title desc">'
        '<title id="title">Kaisar Sofi GitHub contributions</title>'
        '<desc id="desc">Animated GitHub contribution calendar for the last 53 weeks.</desc>'
        '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}'
        '</style><rect x="1" y="1" width="818" height="170" rx="14" '
        'fill="#0d1117" stroke="#30363d"/>'
        '<text x="26" y="25" font-size="12" fill="#8b949e">CONTRIBUTIONS </text>'
        '<text x="155" y="25" font-size="12" fill="#58a6ff">// LAST 53 WEEKS</text>'
        f'{months}'
        '<text x="22" y="52" font-size="9" fill="#8b949e">SUN</text>'
        '<text x="22" y="80" font-size="9" fill="#8b949e">TUE</text>'
        '<text x="22" y="108" font-size="9" fill="#8b949e">THU</text>'
        '<text x="22" y="136" font-size="9" fill="#8b949e">SAT</text>'
        f'{"".join(cells)}'
        f'<text x="52" y="158" font-size="10" fill="#8b949e">{count_label}</text>'
        '<text x="662" y="158" font-size="10" fill="#8b949e">LESS</text>'
        '<rect x="693" y="150" width="10" height="10" rx="2" fill="#161b22"/>'
        '<rect x="709" y="150" width="10" height="10" rx="2" fill="#0e4429"/>'
        '<rect x="725" y="150" width="10" height="10" rx="2" fill="#26a641"/>'
        '<rect x="741" y="150" width="10" height="10" rx="2" fill="#39d353"/>'
        '<text x="759" y="158" font-size="10" fill="#8b949e">MORE</text></svg>\n'
    )


def main():
    days = fetch_days()
    today = datetime.now(timezone.utc).date()
    output = Path(__file__).resolve().parents[1] / "assets" / "contributions.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(days, today), encoding="utf-8")
    print(f"Updated {output.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
