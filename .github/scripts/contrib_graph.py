"""Render the contribution calendar as an SVG (run by the snake workflow)."""
import json
import os
import urllib.request
from datetime import datetime

USER = os.environ.get("GH_USER", "")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = os.environ.get("OUT", "dist/contrib-graph.svg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

COLORS = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353",
}
CELL, GAP, LEFT, TOP = 11, 3, 30, 22


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal):
    weeks = cal["weeks"]
    width = LEFT + len(weeks) * (CELL + GAP) + 10
    height = TOP + 7 * (CELL + GAP) + 24
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="monospace" font-size="10">']
    p.append(f'<rect width="{width}" height="{height}" rx="6" fill="#000000"/>')
    p.append(f'<text x="{LEFT}" y="{height - 6}" fill="#00ff41">{cal["totalContributions"]} contributions in the last year</text>')
    last_month = None
    for i, w in enumerate(weeks):
        x = LEFT + i * (CELL + GAP)
        days = w["contributionDays"]
        if days:
            m = datetime.strptime(days[0]["date"], "%Y-%m-%d").strftime("%b")
            if m != last_month:
                p.append(f'<text x="{x}" y="12" fill="#8b949e">{m}</text>')
                last_month = m
        for d in days:
            wd = (datetime.strptime(d["date"], "%Y-%m-%d").isoweekday()) % 7
            y = TOP + wd * (CELL + GAP)
            c = COLORS.get(d["contributionLevel"], COLORS["NONE"])
            p.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"><title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    for label, wd in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        p.append(f'<text x="0" y="{TOP + wd * (CELL + GAP) + 9}" fill="#8b949e">{label}</text>')
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    cal = fetch()
    with open(OUT, "w") as f:
        f.write(render(cal))
    print("wrote", OUT, cal["totalContributions"], "contributions")
